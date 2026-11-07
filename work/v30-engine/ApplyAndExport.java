import ghidra.app.decompiler.*;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.SourceType;
import ghidra.util.task.ConsoleTaskMonitor;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

/** Args: names.tsv outdir threads. Applies recovered names, then decompiles every function into outdir, grouped by class prefix. */
public class ApplyAndExport extends GhidraScript {
	@Override
	public void run() throws Exception {
		String[] a = getScriptArgs();
		FunctionManager fm = currentProgram.getFunctionManager();
		AddressSpace sp = currentProgram.getAddressFactory().getDefaultAddressSpace();
		int named = 0, created = 0, failed = 0;
		for (String line : Files.readAllLines(Paths.get(a[0]))) {
			String[] p = line.split("\t");
			if (p[0].equals("address")) continue;
			Address ad = sp.getAddress(Long.parseLong(p[0], 16));
			try {
				Function f = fm.getFunctionAt(ad);
				if (f == null) {
					f = createFunction(ad, null);
					if (f == null) { failed++; continue; }
					created++;
				}
				f.setName(p[1], SourceType.ANALYSIS);
				named++;
			} catch (Exception e) { failed++; }
		}
		println("NAMES named " + named + " created " + created + " failed " + failed);

		List<Function> all = new ArrayList<>();
		for (Function f : fm.getFunctions(true)) if (!f.isExternal() && !f.isThunk()) all.add(f);
		int threads = Integer.parseInt(a[2]);
		ExecutorService ex = Executors.newFixedThreadPool(threads);
		BlockingQueue<DecompInterface> pool = new ArrayBlockingQueue<>(threads);
		for (int i = 0; i < threads; i++) {
			DecompInterface d = new DecompInterface();
			d.toggleCCode(true);
			d.toggleSyntaxTree(false);
			d.setSimplificationStyle("decompile");
			if (!d.openProgram(currentProgram)) throw new IOException("decompiler failed to open");
			pool.add(d);
		}
		ConcurrentHashMap<String, ConcurrentSkipListMap<Long, String>> groups = new ConcurrentHashMap<>();
		AtomicInteger ok = new AtomicInteger(), bad = new AtomicInteger(), done = new AtomicInteger();
		long t0 = System.currentTimeMillis();
		for (Function f : all) {
			final Function fn = f;
			ex.submit(() -> {
				DecompInterface d = null;
				try {
					d = pool.take();
					DecompileResults r = d.decompileFunction(fn, 120, new ConsoleTaskMonitor());
					String n = fn.getName();
					int k = n.indexOf("__");
					String g = n.startsWith("FUN_") ? "unnamed_" + String.format("%04x", fn.getEntryPoint().getOffset() >> 16) : (k > 0 ? n.substring(0, k) : "misc");
					long addr = fn.getEntryPoint().getOffset();
					String c;
					if (r != null && r.decompileCompleted() && r.getDecompiledFunction() != null) { c = r.getDecompiledFunction().getC(); ok.incrementAndGet(); }
					else { c = "/* decompile failed: " + (r == null ? "null" : r.getErrorMessage()) + " */\n"; bad.incrementAndGet(); }
					groups.computeIfAbsent(g, x -> new ConcurrentSkipListMap<>()).put(addr, "// " + fn.getEntryPoint() + " " + n + "\n" + c + "\n");
				} catch (Throwable e) {
					bad.incrementAndGet();
				} finally {
					if (d != null) pool.offer(d);
					int v = done.incrementAndGet();
					if (v % 2000 == 0) System.out.println("EXPORT " + v + " of " + all.size() + " ok " + ok.get() + " bad " + bad.get() + " s " + (System.currentTimeMillis() - t0) / 1000);
				}
			});
		}
		ex.shutdown();
		ex.awaitTermination(12, TimeUnit.HOURS);
		for (DecompInterface d : pool) d.dispose();
		Path out = Paths.get(a[1]);
		Files.createDirectories(out);
		long bytes = 0;
		for (Map.Entry<String, ConcurrentSkipListMap<Long, String>> e : groups.entrySet()) {
			String safe = e.getKey().replaceAll("[^A-Za-z0-9_]", "_");
			if (safe.length() > 120) safe = safe.substring(0, 120);
			try (BufferedWriter w = Files.newBufferedWriter(out.resolve(safe + ".c"))) {
				for (String s : e.getValue().values()) { w.write(s); bytes += s.length(); }
			}
		}
		try (PrintWriter w = new PrintWriter(a[1] + "/export-summary.txt")) {
			w.println("functions " + all.size() + " ok " + ok.get() + " failed " + bad.get() + " files " + groups.size() + " bytes " + bytes + " seconds " + (System.currentTimeMillis() - t0) / 1000);
		}
		println("EXPORTDONE ok " + ok.get() + " bad " + bad.get() + " files " + groups.size());
	}
}
