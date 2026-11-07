import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.MemoryBlock;
import java.io.PrintWriter;
import java.util.*;

public class CountFuncs extends GhidraScript {
	@Override
	public void run() throws Exception {
		String out = getScriptArgs()[0];
		FunctionManager fm = currentProgram.getFunctionManager();
		int total = 0, thunks = 0, defaultNamed = 0, inClass = 0;
		long bytes = 0;
		int[] edges = { 16, 64, 256, 1024, 4096, 16384, Integer.MAX_VALUE };
		int[] buckets = new int[edges.length];
		Map<String, Integer> classes = new HashMap<>();
		try (PrintWriter w = new PrintWriter(out + "/functions.tsv", "UTF-8")) {
			w.println("address\tbytes\tthunk\tnamespace\tname");
			for (Function f : fm.getFunctions(true)) {
				if (f.isExternal()) continue;
				total++;
				long n = f.getBody().getNumAddresses();
				if (f.isThunk()) thunks++;
				else {
					bytes += n;
					for (int i = 0; i < edges.length; i++) if (n <= edges[i]) { buckets[i]++; break; }
				}
				String name = f.getName();
				if (name.startsWith("FUN_")) defaultNamed++;
				String ns = f.getParentNamespace().isGlobal() ? "" : f.getParentNamespace().getName(true);
				if (!ns.isEmpty()) { inClass++; classes.merge(ns, 1, Integer::sum); }
				w.println(f.getEntryPoint() + "\t" + n + "\t" + f.isThunk() + "\t" + ns + "\t" + name);
			}
		}
		MemoryBlock text = currentProgram.getMemory().getBlock(".text");
		try (PrintWriter w = new PrintWriter(out + "/functions-summary.txt", "UTF-8")) {
			w.println("functions " + total + " thunks " + thunks + " default_named " + defaultNamed + " in_namespace " + inClass);
			w.println("function_bytes " + bytes + " text_bytes " + text.getSize());
			w.println("size_buckets_le " + Arrays.toString(edges) + " " + Arrays.toString(buckets));
			w.println("namespaces " + classes.size());
		}
		println("COUNTFUNCS done " + total);
	}
}
