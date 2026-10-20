"""Run the bounded VREX-TETHER mechanical controls without opening the game UI."""
import json
import machines
import vrex

if __name__=='__main__':
    print(json.dumps(machines.diagnostics(vrex.new('rose-physics-controls')),indent=2))
