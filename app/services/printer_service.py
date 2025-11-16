"""
Receipt Printer Service for Shopping Lists.

This service handles printing shopping lists to ESC/POS thermal receipt printers
via network connection (Raw TCP/IP on port 9100).
"""

import socket
from datetime import datetime
from typing import Optional, List, Tuple
from flask import current_app

try:
    from escpos.printer import Network
    from escpos.exceptions import Error as EscposError
    ESCPOS_AVAILABLE = True
except ImportError:
    ESCPOS_AVAILABLE = False


class PrinterService:
    """Service for printing shopping lists to thermal receipt printers."""

    def __init__(self):
        """Initialize printer service with configuration from Flask app."""
        self.enabled = current_app.config.get('PRINTER_ENABLED', False)
        self.host = current_app.config.get('PRINTER_HOST', '192.168.1.230')
        self.port = current_app.config.get('PRINTER_PORT', 9100)
        self.timeout = current_app.config.get('PRINTER_TIMEOUT', 5)
        self.width = current_app.config.get('PRINTER_WIDTH', 32)

    def is_available(self) -> bool:
        """Check if printer service is available and enabled."""
        if not self.enabled:
            current_app.logger.info("Printer service is disabled in configuration")
            return False

        if not ESCPOS_AVAILABLE:
            current_app.logger.error("python-escpos library not installed")
            return False

        return True

    def get_printer_status(self) -> dict:
        """
        Get detailed printer status including network connectivity.

        Returns:
            Dictionary with detailed status information
        """
        status = {
            'service_available': self.is_available(),
            'network_reachable': False,
            'escpos_connection': False,
            'response_time_ms': None,
            'error_message': None,
            'details': []
        }

        if not status['service_available']:
            status['error_message'] = "Drucker-Service nicht verfügbar oder deaktiviert"
            status['details'].append("Bitte prüfen Sie die PRINTER_ENABLED Einstellung in der .env Datei")
            return status

        # Test 1: Basic Network Reachability (Socket Test)
        try:
            import time
            start_time = time.time()

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.host, self.port))

            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            status['response_time_ms'] = round(response_time, 2)
            sock.close()

            status['network_reachable'] = True
            status['details'].append(f"✓ Netzwerk erreichbar unter {self.host}:{self.port}")
            status['details'].append(f"✓ Antwortzeit: {status['response_time_ms']} ms")

            current_app.logger.info(f"Network test successful: {self.host}:{self.port} ({response_time:.2f}ms)")

        except socket.timeout:
            status['error_message'] = f"Zeitüberschreitung bei Verbindung zu {self.host}:{self.port}"
            status['details'].append(f"✗ Keine Antwort nach {self.timeout} Sekunden")
            status['details'].append("Mögliche Ursachen: Drucker ausgeschaltet, falsche IP-Adresse, Netzwerkprobleme")
            current_app.logger.error(status['error_message'])
            return status

        except socket.error as e:
            status['error_message'] = f"Verbindungsfehler zu {self.host}:{self.port}"
            status['details'].append(f"✗ Socket-Fehler: {str(e)}")
            status['details'].append("Mögliche Ursachen: Port blockiert, Firewall, falscher Port")
            current_app.logger.error(f"{status['error_message']}: {e}")
            return status

        except Exception as e:
            status['error_message'] = f"Unerwarteter Fehler beim Netzwerk-Test"
            status['details'].append(f"✗ Fehler: {str(e)}")
            current_app.logger.error(f"{status['error_message']}: {e}")
            return status

        # Test 2: ESC/POS Connection Test (only if network is reachable)
        if status['network_reachable'] and ESCPOS_AVAILABLE:
            try:
                printer = Network(self.host, self.port, timeout=self.timeout)
                # Try to initialize - this will fail if it's not an ESC/POS printer
                printer.close()

                status['escpos_connection'] = True
                status['details'].append("✓ ESC/POS Verbindung erfolgreich")
                current_app.logger.info("ESC/POS connection test successful")

            except Exception as e:
                status['details'].append(f"⚠ ESC/POS Verbindung fehlgeschlagen: {str(e)}")
                status['details'].append("Hinweis: Netzwerk ist erreichbar, aber ESC/POS Protokoll antwortet nicht korrekt")
                current_app.logger.warning(f"ESC/POS connection failed: {e}")

        return status

    def test_connection(self) -> Tuple[bool, str]:
        """
        Test connection to the printer.

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.is_available():
            return False, "Drucker-Service nicht verfügbar oder deaktiviert"

        try:
            # Test basic network connectivity
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.host, self.port))
            sock.close()

            current_app.logger.info(f"Printer connection test successful: {self.host}:{self.port}")
            return True, f"Verbindung zu Drucker erfolgreich ({self.host}:{self.port})"

        except socket.timeout:
            msg = f"Zeitüberschreitung bei Verbindung zu {self.host}:{self.port}"
            current_app.logger.error(msg)
            return False, msg

        except socket.error as e:
            msg = f"Verbindungsfehler zu {self.host}:{self.port}: {str(e)}"
            current_app.logger.error(msg)
            return False, msg

        except Exception as e:
            msg = f"Unerwarteter Fehler beim Drucker-Test: {str(e)}"
            current_app.logger.error(msg)
            return False, msg

    def print_test_page(self) -> Tuple[bool, str]:
        """
        Print a test page to verify printer functionality.

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.is_available():
            return False, "Drucker-Service nicht verfügbar"

        try:
            printer = Network(self.host, self.port, timeout=self.timeout)

            # Print test page
            printer.set(align='center', text_type='B', width=2, height=2)
            printer.text("TESTDRUCK\n")

            printer.set(align='center', text_type='normal')
            printer.text("=" * self.width + "\n\n")

            printer.set(align='left')
            printer.text(f"Datum: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
            printer.text(f"Drucker: {self.host}:{self.port}\n")
            printer.text(f"Breite: {self.width} Zeichen\n\n")

            printer.text("Dieser Testdruck bestätigt, dass\n")
            printer.text("die Verbindung zum Bondrucker\n")
            printer.text("erfolgreich hergestellt wurde.\n\n")

            printer.set(align='center')
            printer.text("=" * self.width + "\n")
            printer.text("Einkaufsliste App\n")
            printer.text("www.flgl.tech\n")

            # Cut paper
            printer.cut()
            printer.close()

            current_app.logger.info("Test page printed successfully")
            return True, "Testseite erfolgreich gedruckt"

        except EscposError as e:
            msg = f"ESC/POS Fehler beim Testdruck: {str(e)}"
            current_app.logger.error(msg)
            return False, msg

        except Exception as e:
            msg = f"Fehler beim Testdruck: {str(e)}"
            current_app.logger.error(msg)
            return False, msg

    def print_shopping_list(self, shopping_list, include_checked: bool = False) -> Tuple[bool, str]:
        """
        Print a shopping list to the thermal receipt printer.

        Args:
            shopping_list: ShoppingList model instance
            include_checked: If True, also print checked items (default: False)

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.is_available():
            return False, "Drucker-Service nicht verfügbar"

        try:
            # Get items to print
            items = shopping_list.items
            if not include_checked:
                items = [item for item in items if not item.checked]

            if not items:
                return False, "Keine Artikel zum Drucken (alle abgehakt)"

            # Connect to printer
            printer = Network(self.host, self.port, timeout=self.timeout)

            # Format and print the receipt
            self._print_header(printer, shopping_list)
            self._print_items(printer, items)
            self._print_footer(printer)

            # Cut paper and close connection
            printer.cut()
            printer.close()

            current_app.logger.info(
                f"Shopping list '{shopping_list.title}' (ID: {shopping_list.id}) "
                f"printed successfully with {len(items)} items"
            )
            return True, f"Liste '{shopping_list.title}' erfolgreich gedruckt ({len(items)} Artikel)"

        except EscposError as e:
            msg = f"ESC/POS Fehler beim Drucken: {str(e)}"
            current_app.logger.error(msg)
            return False, msg

        except Exception as e:
            msg = f"Fehler beim Drucken der Liste: {str(e)}"
            current_app.logger.error(msg)
            return False, msg

    def _print_header(self, printer, shopping_list):
        """Print receipt header with list title and date."""
        # Title (large, bold, centered)
        printer.set(align='center', text_type='B', width=2, height=2)

        # Wrap title if too long
        title = shopping_list.title
        if len(title) > 16:  # Half width due to double-width
            title = title[:13] + "..."

        printer.text(f"{title}\n")

        # Separator
        printer.set(align='center', text_type='normal')
        printer.text("=" * self.width + "\n\n")

        # Date and time
        printer.set(align='left')
        now = datetime.now()
        printer.text(f"Datum: {now.strftime('%d.%m.%Y %H:%M')}\n")

        # Owner information
        if shopping_list.user:
            printer.text(f"Erstellt von: {shopping_list.user.username}\n")

        printer.text("\n")

    def _print_items(self, printer, items: List):
        """Print shopping list items."""
        printer.set(align='left', text_type='normal')

        for item in items:
            # Checkbox symbol
            checkbox = "☑" if item.checked else "☐"

            # Format quantity
            quantity_str = ""
            if item.quantity and item.quantity > 1:
                quantity_str = f"{item.quantity}x "

            # Item name (truncate if too long)
            # Reserve 4 chars for checkbox and spacing, some for quantity
            max_name_length = self.width - 4 - len(quantity_str)
            name = item.name
            if len(name) > max_name_length:
                name = name[:max_name_length - 3] + "..."

            # Print item line
            line = f"{checkbox} {quantity_str}{name}\n"

            # If checked, use strikethrough effect (print with different style)
            if item.checked:
                printer.set(text_type='U')  # Underlined as strikethrough alternative
                printer.text(line)
                printer.set(text_type='normal')
            else:
                printer.text(line)

        printer.text("\n")

    def _print_footer(self, printer):
        """Print receipt footer."""
        printer.set(align='center', text_type='normal')
        printer.text("=" * self.width + "\n\n")

        printer.set(text_type='B')
        printer.text("Viel Erfolg beim Einkauf!\n\n")

        printer.set(text_type='normal')
        printer.text("Einkaufsliste App\n")
        printer.text(datetime.now().strftime('%d.%m.%Y %H:%M:%S') + "\n\n")


def get_printer_service() -> PrinterService:
    """
    Factory function to get a PrinterService instance.

    Returns:
        PrinterService instance
    """
    return PrinterService()
