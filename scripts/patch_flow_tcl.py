import os
import subprocess

# Read flow.tcl via WSL
get_cmd = ["wsl", "-e", "cat", "/home/sujan123/rtl2gds/OpenLane/flow.tcl"]
content = subprocess.check_output(get_cmd, text=True)

target = "set ::env(OPENLANE_ROOT) [file dirname [file normalize [info script]]]"
wrapper = """set ::env(OPENLANE_ROOT) [file dirname [file normalize [info script]]]

# Autonomous Docker Dispatch Wrapper
if { ! [file exists "/.dockerenv"] && ! [info exists ::env(OPENLANE_IN_DOCKER)] } {
    set docker_image "ghcr.io/the-openroad-project/openlane:ff5509f65b17bfa4068d5336495ab1718987ff69-amd64"
    set home_dir $::env(HOME)
    set openlane_dir $::env(OPENLANE_ROOT)
    set pdk_dir "$home_dir/.ciel"
    set cmd [list docker run --rm \\
        -v "$openlane_dir:/openlane" \\
        -v "$openlane_dir/designs:/openlane/install" \\
        -v "$home_dir:$home_dir" \\
        -v "$pdk_dir:$pdk_dir" \\
        -e "PDK_ROOT=$pdk_dir" \\
        -e "PDK=sky130A" \\
        -e "OPENLANE_IN_DOCKER=1" \\
        --user "1000:1000" \\
        $docker_image \\
        ./flow.tcl {*}$argv]
    set code [catch {exec >@stdout 2>@stderr {*}$cmd} result]
    exit $code
}"""

if "# Autonomous Docker Dispatch Wrapper" not in content:
    content = content.replace(target, wrapper, 1)
    # Write temp file and move in wsl
    temp_path = "scripts/flow.tcl.tmp"
    with open(temp_path, "w", newline="\n") as f:
        f.write(content)
    subprocess.check_call(["wsl", "-e", "cp", f"/mnt/c/Users/ssuja/OneDrive/Desktop/Learn_Antigravity_Advance/rtl-2-gds-automation-local-llm/{temp_path}", "/home/sujan123/rtl2gds/OpenLane/flow.tcl"])
    os.remove(temp_path)
    print("flow.tcl wrapper successfully installed!")
else:
    print("flow.tcl wrapper already present.")
