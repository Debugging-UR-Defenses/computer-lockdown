"""
Network rules management for Computer Lockdown.

Manages Windows Firewall rules to control which network services are allowed
when the system is in locked mode. Supports allowing specific LAN services
by port/protocol, and blocking outbound connections to unauthorized ports.
"""

import logging
import platform
from typing import Optional

from ..utils.config import ConfigManager
from ..utils.subprocess_helper import run_hidden

logger = logging.getLogger(__name__)

_IS_WINDOWS = platform.system() == "Windows"


class NetworkRules:
    """Manages network/firewall rules for lockdown mode.
    
    Allows specific LAN services (like printer communication, local DNS)
    to continue working while blocking unauthorized network activity.
    """
    
    RULE_PREFIX = "ComputerLockdown_"
    
    def __init__(self, config_manager: ConfigManager) -> None:
        self.config = config_manager
        self._applied_rules: list[str] = []
    
    def apply_rules(self) -> None:
        """Apply all configured network rules via Windows Firewall."""
        if not self.config.get("network_rules.enabled", False):
            logger.info("Network rules are disabled in config.")
            return
        
        # First remove any existing rules we created
        self.remove_rules()
        
        allowed_services = self.config.get("network_rules.allowed_lan_services", [])
        blocked_ports = self.config.get("network_rules.blocked_ports", [])
        
        for svc in allowed_services:
            self._add_allow_rule(svc)
        
        for port_info in blocked_ports:
            self._add_block_rule(port_info)
        
        logger.info("Network rules applied: %d allow, %d block", 
                     len(allowed_services), len(blocked_ports))
    
    def remove_rules(self) -> None:
        """Remove all Computer Lockdown firewall rules."""
        if not _IS_WINDOWS:
            logger.debug("Dry-run: would remove firewall rules.")
            self._applied_rules.clear()
            return
        
        # Remove rules by prefix
        try:
            result = run_hidden(
                ["netsh", "advfirewall", "firewall", "show", "rule",
                 f"name=all"],
                capture_output=True, text=True, timeout=10,
            )
            for line in result.stdout.splitlines():
                if self.RULE_PREFIX in line:
                    rule_name = line.split(":", 1)[-1].strip() if ":" in line else ""
                    if rule_name:
                        self._delete_rule(rule_name)
        except Exception:
            logger.exception("Error removing firewall rules.")
        
        self._applied_rules.clear()
        logger.info("All Computer Lockdown firewall rules removed.")
    
    def _add_allow_rule(self, service: dict) -> None:
        """Add a firewall allow rule for a LAN service."""
        name = service.get("name", "Unknown")
        protocol = service.get("protocol", "tcp")
        port = service.get("port", 0)
        
        if not port:
            return
        
        rule_name = f"{self.RULE_PREFIX}Allow_{name.replace(' ', '_')}"
        
        if not _IS_WINDOWS:
            logger.debug("Dry-run: would add allow rule '%s' for %s/%d", 
                         rule_name, protocol, port)
            self._applied_rules.append(rule_name)
            return
        
        try:
            # Allow inbound
            run_hidden(
                ["netsh", "advfirewall", "firewall", "add", "rule",
                 f"name={rule_name}_In", "dir=in", f"action=allow",
                 f"protocol={protocol}", f"localport={port}"],
                capture_output=True, text=True, timeout=10,
            )
            # Allow outbound
            run_hidden(
                ["netsh", "advfirewall", "firewall", "add", "rule",
                 f"name={rule_name}_Out", "dir=out", f"action=allow",
                 f"protocol={protocol}", f"remoteport={port}"],
                capture_output=True, text=True, timeout=10,
            )
            self._applied_rules.append(rule_name)
            logger.info("Added allow rule: %s (%s/%d)", name, protocol, port)
        except Exception:
            logger.exception("Failed to add allow rule for %s.", name)
    
    def _add_block_rule(self, port_info: dict) -> None:
        """Add a firewall block rule for a specific port."""
        protocol = port_info.get("protocol", "tcp")
        port = port_info.get("port", 0)
        description = port_info.get("description", "")
        
        if not port:
            return
        
        rule_name = f"{self.RULE_PREFIX}Block_{protocol}_{port}"
        
        if not _IS_WINDOWS:
            logger.debug("Dry-run: would add block rule '%s'", rule_name)
            self._applied_rules.append(rule_name)
            return
        
        try:
            run_hidden(
                ["netsh", "advfirewall", "firewall", "add", "rule",
                 f"name={rule_name}", "dir=out", "action=block",
                 f"protocol={protocol}", f"remoteport={port}"],
                capture_output=True, text=True, timeout=10,
            )
            self._applied_rules.append(rule_name)
            logger.info("Added block rule: %s/%d (%s)", protocol, port, description)
        except Exception:
            logger.exception("Failed to add block rule for %s/%d.", protocol, port)
    
    def _delete_rule(self, rule_name: str) -> None:
        """Delete a specific firewall rule by name."""
        if not _IS_WINDOWS:
            return
        try:
            run_hidden(
                ["netsh", "advfirewall", "firewall", "delete", "rule",
                 f"name={rule_name}"],
                capture_output=True, text=True, timeout=10,
            )
        except Exception:
            logger.debug("Failed to delete rule: %s", rule_name)
    
    def get_applied_rules(self) -> list[str]:
        """Return list of currently applied rule names."""
        return list(self._applied_rules)
    
    def get_status(self) -> dict:
        """Return status of network rules."""
        return {
            "enabled": self.config.get("network_rules.enabled", False),
            "rules_applied": len(self._applied_rules),
            "allowed_services": len(self.config.get("network_rules.allowed_lan_services", [])),
            "blocked_ports": len(self.config.get("network_rules.blocked_ports", [])),
        }
