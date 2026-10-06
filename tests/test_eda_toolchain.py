#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_eda_toolchain.py
===========================
Automated Audit & Verification for Local/WSL EDA Toolchain:
  1. Icarus Verilog compiler (iverilog) & Simulation runtime (vvp)
  2. Yosys Logic Synthesis Engine (yosys)
  3. KLayout Layout Inspection Engine (klayout)
  4. Verilator Lint Engine (verilator)
"""

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.resolve()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from wsl_tool_runner import (
    check_wsl_tools,
    run_iverilog_sim,
    run_yosys_synth,
    run_verilator_lint,
    _run_wsl,
    _wsl_path,
)


class TestEDAToolchain(unittest.TestCase):
    """Audit suite for EDA tools inside WSL."""

    def test_01_tool_versions(self):
        """Verify that all core EDA tools are present and report versions."""
        tools = check_wsl_tools()
        print("\n[Tool Audit] Discovered EDA Engines in WSL:")
        for tool, ver in tools.items():
            print(f"  - {tool:<12}: {ver}")

        self.assertIsNotNone(tools.get("iverilog"), "iverilog must be installed in WSL")
        self.assertIsNotNone(tools.get("vvp"), "vvp must be installed in WSL")
        self.assertIsNotNone(tools.get("yosys"), "yosys must be installed in WSL")

    def test_02_iverilog_and_vvp_simulation(self):
        """Verify iverilog compilation and vvp simulation execution."""
        sample_v = """
module smoke_counter (
    input clk,
    input rst,
    output reg [3:0] q
);
    always @(posedge clk or posedge rst) begin
        if (rst)
            q <= 4'b0000;
        else
            q <= q + 1'b1;
    end
endmodule
"""
        sample_tb = """
`timescale 1ns/1ps
module smoke_counter_tb;
    reg clk, rst;
    wire [3:0] q;
    integer passed_tests = 0;
    integer total_tests = 0;

    smoke_counter dut (.clk(clk), .rst(rst), .q(q));

    always #5 clk = ~clk;

    initial begin
        clk = 0;
        rst = 1;
        #20;
        rst = 0;
        #10;
        total_tests = total_tests + 1;
        if (q == 4'd1) passed_tests = passed_tests + 1;
        #10;
        total_tests = total_tests + 1;
        if (q == 4'd2) passed_tests = passed_tests + 1;

        $display("TEST PASSED: %0d/%0d", passed_tests, total_tests);
        if (passed_tests == total_tests) $display("SIMULATION RESULT: PASSED");
        else $display("SIMULATION RESULT: FAILED");
        $finish;
    end
endmodule
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            v_file = Path(tmpdir) / "smoke_counter.v"
            tb_file = Path(tmpdir) / "smoke_counter_tb.v"
            v_file.write_text(sample_v, encoding="utf-8")
            tb_file.write_text(sample_tb, encoding="utf-8")

            sim = run_iverilog_sim(str(v_file), str(tb_file), top_module="smoke_counter_tb")
            print(f"\n[iverilog+vvp Output]:\n{sim.output}")

            self.assertTrue(sim.passed, "Simulation did not pass")
            self.assertTrue(sim.finish_reached, "$finish was not reached in simulation")
            self.assertEqual(sim.assertions_passed, 2, "Expected 2 assertions to pass")

    def test_03_yosys_logic_synthesis(self):
        """Verify Yosys gate-level logic synthesis and cell mapping."""
        sample_v = """
module smoke_alu (
    input [3:0] a,
    input [3:0] b,
    input op,
    output [3:0] y
);
    assign y = op ? (a & b) : (a + b);
endmodule
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            v_file = Path(tmpdir) / "smoke_alu.v"
            v_file.write_text(sample_v, encoding="utf-8")

            out_netlist = Path(tmpdir) / "smoke_alu_netlist.v"
            synth = run_yosys_synth(
                verilog_file=str(v_file),
                top_module="smoke_alu",
                output_netlist=str(out_netlist),
            )
            print(f"\n[Yosys Stats]: Cell count = {synth.cell_count}, Wires = {synth.wire_count}")
            print(f"[Yosys Cells]: {synth.cell_breakdown}")

            self.assertTrue(synth.success, "Yosys synthesis failed")
            self.assertGreater(synth.cell_count, 0, "No cells were synthesized")
            self.assertTrue(Path(synth.netlist_path).exists(), "Synthesized netlist was not created")

    def test_04_klayout_presence(self):
        """Verify KLayout CLI execution."""
        r = _run_wsl("klayout -v", timeout=10)
        self.assertTrue(r.success, "klayout -v execution failed")
        print(f"\n[KLayout CLI]: {r.stdout.strip()}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
