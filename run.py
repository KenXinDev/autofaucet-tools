import os
import sys
import subprocess
import json
import platform
from pathlib import Path

class MinerApp:
    def __init__(self):
        self.system = platform.system().lower()
        self.is_termux = '/com.termux/' in os.environ.get('PATH', '')
        self.colors = {
            'HEADER': '\033[95m',
            'OKBLUE': '\033[94m',
            'OKCYAN': '\033[96m',
            'OKGREEN': '\033[92m',
            'WARNING': '\033[93m',
            'FAIL': '\033[91m',
            'ENDC': '\033[0m',
            'BOLD': '\033[1m',
            'UNDERLINE': '\033[4m'
        }

    def print_header(self):
        print(f"""
{self.colors['OKGREEN']}
███████╗███╗   ███╗██████╗     ███╗   ███╗██╗███╗   ██╗███████╗██████╗ 
██╔════╝████╗ ████║██╔══██╗    ████╗ ████║██║████╗  ██║██╔════╝██╔══██╗
█████╗  ██╔████╔██║██████╔╝    ██╔████╔██║██║██╔██╗ ██║█████╗  ██║  ██║
██╔══╝  ██║╚██╔╝██║██╔══██╗    ██║╚██╔╝██║██║██║╚██╗██║██╔══╝  ██║  ██║
███████╗██║ ╚═╝ ██║██║  ██║    ██║ ╚═╝ ██║██║██║ ╚████║███████╗██████╔╝
╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝    ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚══════╝╚═════╝ 
{self.colors['ENDC']}
        {self.colors['BOLD']}XMRig Manager v1.2 - Linux/Termux by KenXinDev{self.colors['ENDC']}
        """)

    def print_status(self, message, status="info"):
        symbols = {
            "info": f"{self.colors['OKBLUE']}[i]{self.colors['ENDC']}",
            "success": f"{self.colors['OKGREEN']}[✓]{self.colors['ENDC']}",
            "error": f"{self.colors['FAIL']}[✗]{self.colors['ENDC']}",
            "warning": f"{self.colors['WARNING']}[!]{self.colors['ENDC']}"
        }
        print(f"{symbols[status]} {message}")

    def validate_config(self, config_path):
        try:
            with open(config_path) as f:
                config = json.load(f)

            required = {
                'pools': list,
                'cpu': dict
            }

            for field, field_type in required.items():
                if field not in config:
                    raise ValueError(f"Missing required field: {field}")
                if not isinstance(config[field], field_type):
                    raise ValueError(f"Invalid type for {field}, expected {field_type.__name__}")

            for i, pool in enumerate(config['pools']):
                if not pool.get('url'):
                    raise ValueError(f"Pool #{i+1} missing 'url'")
                if not pool.get('user'):
                    raise ValueError(f"Pool #{i+1} missing 'user'")

            self.print_status("Config file validation passed", "success")
            return True

        except Exception as e:
            self.print_status(f"Config error: {str(e)}", "error")
            sys.exit(1)

    def install_dependencies(self):
        try:
            if self.is_termux:
                self.print_status("Installing Termux dependencies...")
                subprocess.run(
                    ['pkg', 'install', '-y', 'git', 'cmake', 'make', 'libuv-static', 'binutils'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True
                )
            else:
                self.print_status("Installing Linux dependencies...")
                subprocess.run(
                    ['sudo', 'apt-get', 'update', '-y'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True
                )
                subprocess.run(
                    ['sudo', 'apt-get', 'install', '-y', 'git', 'build-essential', 'cmake', 'libuv1-dev', 'libssl-dev', 'libhwloc-dev'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True
                )
            self.print_status("Dependencies installed successfully", "success")
        except subprocess.CalledProcessError as e:
            self.print_status(f"Installation failed: {str(e)}", "error")
            sys.exit(1)

    def build_xmrig(self):
        try:
            if not Path("xmrig").exists():
                self.print_status("Cloning XMRig repository...")
                subprocess.run(
                    ['git', 'clone', 'https://github.com/xmrig/xmrig.git'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True
                )

            os.chdir("xmrig")
            if not Path("build").exists():
                os.makedirs("build")

            os.chdir("build")
            self.print_status("Building XMRig (this may take several minutes)...")
            subprocess.run(
                ['cmake', '..'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            subprocess.run(
                ['make'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            os.chdir("../..")
            self.print_status("XMRig built successfully", "success")

        except subprocess.CalledProcessError as e:
            self.print_status(f"Build failed: {str(e)}", "error")
            sys.exit(1)

    def run_miner(self, config_path):
        try:
            cmd = ['./xmrig/build/xmrig', '-c', config_path]
            self.print_status("Starting mining process...", "info")
            print(f"{self.colors['OKCYAN']}=== Mining Session Started ==={self.colors['ENDC']}")

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )

            keywords = ['accepted', 'cpu', 'net', 'miner', 'speed', 'shares']

            for line in process.stdout:
                lower_line = line.lower()
                if any(keyword in lower_line for keyword in keywords):
                    if 'accepted' in lower_line:
                        print(f"{self.colors['OKGREEN']}{line.strip()}{self.colors['ENDC']}")
                    elif 'error' in lower_line:
                        print(f"{self.colors['FAIL']}{line.strip()}{self.colors['ENDC']}")
                    elif 'speed' in lower_line or 'shares' in lower_line:
                        print(f"{self.colors['OKBLUE']}{line.strip()}{self.colors['ENDC']}")
                    else:
                        print(line.strip())
            process.wait()

        except KeyboardInterrupt:
            self.print_status("\nMining stopped by user", "warning")
            process.terminate()
        except Exception as e:
            self.print_status(f"Runtime error: {str(e)}", "error")
            sys.exit(1)

    def main(self):
        self.print_header()

        if len(sys.argv) < 2:
            self.print_status("Usage: python3 run.py <config.json>", "error")
            self.print_status("Optional flags: --install-deps (force install dependencies)", "info")
            sys.exit(1)

        config_path = Path(sys.argv[1])

        if not config_path.exists():
            self.print_status(f"Config file not found: {config_path}", "error")
            sys.exit(1)

        self.validate_config(config_path)

        if '--install-deps' in sys.argv:
            self.install_dependencies()

        if not Path("xmrig/build/xmrig").exists():
            self.print_status("XMRig not detected", "warning")
            if input("Install dependencies and build XMRig? [Y/n]: ").lower() in ('y', ''):
                self.install_dependencies()
                self.build_xmrig()
            else:
                self.print_status("Aborted by user", "error")
                sys.exit(0)

        self.run_miner(config_path)

if __name__ == "__main__":
    app = MinerApp()
    app.main()
