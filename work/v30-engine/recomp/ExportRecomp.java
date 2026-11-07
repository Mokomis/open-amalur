import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import java.io.PrintWriter;

/** Args: outdir. Writes each function's address ranges and the targets of every computed jump. */
public class ExportRecomp extends GhidraScript {
	@Override
	public void run() throws Exception {
		String out = getScriptArgs()[0];
		Listing listing = currentProgram.getListing();
		int funcs = 0, tables = 0, unresolved = 0;
		try (PrintWriter f = new PrintWriter(out + "/func_ranges.tsv", "UTF-8");
				PrintWriter j = new PrintWriter(out + "/computed_jumps.tsv", "UTF-8")) {
			for (Function fn : currentProgram.getFunctionManager().getFunctions(true)) {
				if (fn.isExternal()) continue;
				StringBuilder sb = new StringBuilder();
				for (AddressRange r : fn.getBody()) {
					if (sb.length() > 0) sb.append(',');
					sb.append(r.getMinAddress()).append('-').append(r.getMaxAddress());
				}
				f.println(fn.getEntryPoint() + "\t" + fn.isThunk() + "\t" + sb);
				funcs++;
				for (Instruction in : listing.getInstructions(fn.getBody(), true)) {
					if (in.getFlowType().isComputed() && in.getFlowType().isJump()) {
						Address[] flows = in.getFlows();
						StringBuilder t = new StringBuilder();
						for (Address a : flows) {
							if (t.length() > 0) t.append(',');
							t.append(a);
						}
						j.println(in.getAddress() + "\t" + fn.getEntryPoint() + "\t" + t);
						if (flows.length == 0) unresolved++;
						else tables++;
					}
				}
			}
		}
		println("RECOMPEXPORT functions " + funcs + " computed jumps resolved " + tables + " unresolved " + unresolved);
	}
}
