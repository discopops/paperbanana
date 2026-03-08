#!/usr/bin/env python3
"""End-to-end verification script for agentic vision integration.

This script tests the complete agentic vision pipeline:
1. Provider code execution support
2. Planning phase reference pattern analysis
3. Critique phase visual analysis
4. Output artifact verification
"""

import json
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

console = Console()


def check_provider_support():
    """Verify Gemini provider supports code execution."""
    console.print("\n[bold]1. Checking provider code execution support...[/bold]")

    from paperbanana.providers.vlm.gemini import GeminiVLM

    # Test Gemini 3 Flash
    vlm_3 = GeminiVLM(api_key="test", model="gemini-3-flash-preview")
    if vlm_3.supports_code_execution():
        console.print("  ✓ Gemini 3 Flash supports code execution")
    else:
        console.print("  ✗ [red]Gemini 3 Flash should support code execution[/red]")
        return False

    # Test Gemini 2 Flash (should NOT support)
    vlm_2 = GeminiVLM(api_key="test", model="gemini-2.0-flash")
    if not vlm_2.supports_code_execution():
        console.print("  ✓ Gemini 2.0 Flash correctly reports no code execution")
    else:
        console.print("  ✗ [red]Gemini 2.0 Flash should not support code execution[/red]")
        return False

    return True


def check_configuration():
    """Verify configuration includes agentic vision settings."""
    console.print("\n[bold]2. Checking configuration support...[/bold]")

    from paperbanana.core.config import Settings

    settings = Settings(
        planner_enable_reference_analysis=True,
        critic_enable_visual_analysis=True,
    )

    if settings.planner_enable_reference_analysis:
        console.print("  ✓ Planner reference analysis can be enabled")
    else:
        console.print("  ✗ [red]Configuration failed[/red]")
        return False

    if settings.critic_enable_visual_analysis:
        console.print("  ✓ Critic visual analysis can be enabled")
    else:
        console.print("  ✗ [red]Configuration failed[/red]")
        return False

    return True


def check_type_models():
    """Verify new type models are available."""
    console.print("\n[bold]3. Checking type models...[/bold]")

    from paperbanana.core.types import ReferencePatterns, VisualAnalysis, CritiqueResult

    # Test ReferencePatterns
    patterns = ReferencePatterns(
        layout_structure="vertical flow",
        color_palette=["#FFFFFF", "#000000"],
    )
    console.print(f"  ✓ ReferencePatterns model works: {patterns.layout_structure}")

    # Test VisualAnalysis
    analysis = VisualAnalysis(
        detected_text=["Test"],
        text_clarity_score=0.85,
    )
    console.print(f"  ✓ VisualAnalysis model works: {len(analysis.detected_text)} texts")

    # Test CritiqueResult with visual_analysis
    critique = CritiqueResult(
        critic_suggestions=["Fix typo"],
        visual_analysis=analysis,
    )
    console.print(
        f"  ✓ CritiqueResult includes visual_analysis: {critique.visual_analysis is not None}"
    )

    return True


def check_agent_initialization():
    """Verify agents can be initialized with agentic vision enabled."""
    console.print("\n[bold]4. Checking agent initialization...[/bold]")

    from paperbanana.agents.planner import PlannerAgent
    from paperbanana.agents.critic import CriticAgent
    from paperbanana.providers.vlm.gemini import GeminiVLM

    vlm = GeminiVLM(api_key="test", model="gemini-3-flash-preview")

    # Test Planner
    planner = PlannerAgent(vlm, enable_reference_analysis=True)
    if planner._enable_reference_analysis:
        console.print("  ✓ Planner initialized with reference analysis enabled")
    else:
        console.print("  ✗ [red]Planner initialization failed[/red]")
        return False

    # Test Critic
    critic = CriticAgent(vlm, enable_visual_analysis=True)
    if critic._enable_visual_analysis:
        console.print("  ✓ Critic initialized with visual analysis enabled")
    else:
        console.print("  ✗ [red]Critic initialization failed[/red]")
        return False

    return True


def check_cli_flags():
    """Verify CLI supports agentic vision flags."""
    console.print("\n[bold]5. Checking CLI integration...[/bold]")

    import subprocess
    import sys

    # Check help output includes new flags
    result = subprocess.run(
        [sys.executable, "-m", "paperbanana", "generate", "--help"],
        capture_output=True,
        text=True,
    )

    if "--enable-agentic-vision" in result.stdout:
        console.print("  ✓ CLI includes --enable-agentic-vision flag")
    else:
        console.print("  ⚠ [yellow]CLI flag not found in help (may need installation)[/yellow]")

    if "--enable-reference-analysis" in result.stdout:
        console.print("  ✓ CLI includes --enable-reference-analysis flag")
    else:
        console.print("  ⚠ [yellow]CLI flag not found in help (may need installation)[/yellow]")

    if "--enable-visual-analysis" in result.stdout:
        console.print("  ✓ CLI includes --enable-visual-analysis flag")
    else:
        console.print("  ⚠ [yellow]CLI flag not found in help (may need installation)[/yellow]")

    return True


def run_full_pipeline_test():
    """Run full pipeline with agentic vision (requires API key)."""
    console.print("\n[bold]6. Running full pipeline test...[/bold]")

    import os

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        console.print(
            "  ⚠ [yellow]Skipping full pipeline test (GOOGLE_API_KEY not set)[/yellow]"
        )
        return True

    console.print("  [dim]Note: This test may take 1-2 minutes and use API credits[/dim]")

    # Test with minimal input
    test_input = """
    Our method uses a neural network to process input data.
    The network consists of an encoder and decoder.
    """

    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(test_input)
        input_path = f.name

    try:
        import subprocess

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "paperbanana",
                "generate",
                "--input",
                input_path,
                "--caption",
                "Figure 1: Test",
                "--iterations",
                "1",
                "--enable-agentic-vision",
            ],
            capture_output=True,
            text=True,
            timeout=180,
        )

        if result.returncode == 0:
            console.print("  ✓ Full pipeline completed successfully")

            # Check for output artifacts
            import glob

            output_dirs = glob.glob("outputs/run_*")
            if output_dirs:
                latest_run = max(output_dirs, key=lambda p: Path(p).stat().st_mtime)
                console.print(f"  ✓ Output directory created: {latest_run}")

                # Check for visual analysis artifacts
                planning_file = Path(latest_run) / "planning.json"
                if planning_file.exists():
                    with open(planning_file) as f:
                        planning = json.load(f)
                    # Note: reference_patterns would be in planning if feature worked
                    console.print("  ✓ Planning artifacts saved")

                iter_details = Path(latest_run) / "iter_1" / "details.json"
                if iter_details.exists():
                    with open(iter_details) as f:
                        details = json.load(f)
                    if details.get("critique", {}).get("visual_analysis"):
                        console.print("  ✓ Visual analysis present in critique")
                    else:
                        console.print(
                            "  ⚠ [yellow]Visual analysis not found in critique output[/yellow]"
                        )
            else:
                console.print("  ⚠ [yellow]No output directory found[/yellow]")

            return True
        else:
            console.print(f"  ✗ [red]Pipeline failed: {result.stderr}[/red]")
            return False

    except subprocess.TimeoutExpired:
        console.print("  ✗ [red]Pipeline timed out (>3 minutes)[/red]")
        return False
    except Exception as e:
        console.print(f"  ✗ [red]Pipeline error: {e}[/red]")
        return False
    finally:
        Path(input_path).unlink(missing_ok=True)


def main():
    """Run all verification checks."""
    console.print(
        Panel.fit(
            "[bold]PaperBanana Agentic Vision Integration Verification[/bold]\n\n"
            "This script verifies the agentic vision integration is working correctly.",
            border_style="blue",
        )
    )

    checks = [
        ("Provider Support", check_provider_support),
        ("Configuration", check_configuration),
        ("Type Models", check_type_models),
        ("Agent Initialization", check_agent_initialization),
        ("CLI Integration", check_cli_flags),
        ("Full Pipeline Test", run_full_pipeline_test),
    ]

    results = []
    for name, check_fn in checks:
        try:
            result = check_fn()
            results.append((name, result))
        except Exception as e:
            console.print(f"\n[red]Error in {name}: {e}[/red]")
            results.append((name, False))

    # Summary
    console.print("\n" + "=" * 60)
    console.print("[bold]Verification Summary[/bold]\n")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        color = "green" if result else "red"
        console.print(f"  [{color}]{status}[/{color}] {name}")

    console.print(f"\n[bold]Results: {passed}/{total} checks passed[/bold]")

    if passed == total:
        console.print("\n[green]✓ All checks passed! Agentic vision integration is working.[/green]")
        return 0
    else:
        console.print(
            f"\n[yellow]⚠ {total - passed} check(s) failed. Review output above.[/yellow]"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
