import sys
import os.path
import io
import unittest
import pytest
import time
from unittest.mock import patch
import socket

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncping3 as ping3  # noqa: linter (pycodestyle) should not lint this line.
from asyncping3 import errors  # noqa: linter (pycodestyle) should not lint this line.

DEST_DOMAIN = 'example.com'

class TestPing3:
    """ping3 unittest"""

    @pytest.mark.anyio
    async def test_ping_normal(self):
        delay = await ping3.ping(DEST_DOMAIN)
        self.assertIsInstance(delay, float)

    @pytest.mark.anyio
    async def test_verbose_ping_normal(self):
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            await ping3.verbose_ping(DEST_DOMAIN)
            self.assertRegex(fake_out.getvalue(), r".*[0-9]+ms.*")

    @pytest.mark.anyio
    async def test_ping_timeout(self):
        ping3.EXCEPTIONS = False
        delay = await ping3.ping(DEST_DOMAIN, timeout=0.0001)
        self.assertIsNone(delay)

    @pytest.mark.anyio
    async def test_ping_timeout_exception(self):
        ping3.EXCEPTIONS = True
        with self.assertRaises(errors.Timeout):
            await ping3.ping(DEST_DOMAIN, timeout=0.0001)

    @pytest.mark.anyio
    async def test_verbose_ping_timeout(self):
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            ping3.EXCEPTIONS = False
            await ping3.verbose_ping(DEST_DOMAIN, timeout=0.0001)
            self.assertRegex(fake_out.getvalue(), r".*Timeout \> [0-9\.]+s.*")

    @pytest.mark.anyio
    async def test_verbose_ping_timeout_exception(self):
        with patch("sys.stdout", new=io.StringIO()):
            ping3.EXCEPTIONS = True
            with self.assertRaises(errors.Timeout):
                await ping3.verbose_ping(DEST_DOMAIN, timeout=0.0001)

    @pytest.mark.anyio
    async def test_ping_error(self):
        delay = await ping3.ping("not.exist.com")
        self.assertFalse(delay)

    @pytest.mark.anyio
    async def test_ping_error_exception(self):
        with patch("ping3.EXCEPTIONS", True):
            try:
                await ping3.ping("not.exist.com")
            except ping3.errors.HostUnknown as e:
                self.assertEqual(e.dest_addr, "not.exist.com")

    @pytest.mark.anyio
    async def test_ping_seq(self):
        delay = await ping3.ping(DEST_DOMAIN, seq=199)
        self.assertIsInstance(delay, float)

    @pytest.mark.anyio
    async def test_ping_size(self):
        delay = await ping3.ping(DEST_DOMAIN, size=100)
    def test_ping_size(self):
        delay = ping3.ping(DEST_DOMAIN, size=100)
        self.assertIsInstance(delay, float)

    async def test_ping_size_exception(self):
        with self.assertRaises(OSError):
            await ping3.ping(DEST_DOMAIN, size=99999)  # most router has 1480 MTU, which is IP_Header(20) + ICMP_Header(8) + ICMP_Payload(1452)

    @pytest.mark.anyio
    async def test_verbose_ping_size(self):
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            await ping3.verbose_ping(DEST_DOMAIN, size=100)
            self.assertRegex(fake_out.getvalue(), r".*[0-9]+ms.*")

    @pytest.mark.anyio
    async def test_verbose_ping_size_exception(self):
        with self.assertRaises(OSError):
            await ping3.verbose_ping(DEST_DOMAIN, size=99999)

    @pytest.mark.anyio
    async def test_ping_unit(self):
        delay = await ping3.ping(DEST_DOMAIN, unit="ms")
        self.assertIsInstance(delay, float)
        self.assertTrue(delay > 1)

    @pytest.mark.anyio
    async def test_verbose_ping_unit(self):
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            await ping3.verbose_ping(DEST_DOMAIN, unit="ms")
            self.assertRegex(fake_out.getvalue(), r".*[0-9]+ms.*")

    @unittest.skipUnless(sys.platform == "linux", "Linux only")
    @pytest.mark.anyio
    async def test_ping_interface(self):
        try:
            route_cmd = os.popen("ip -o -4 route show to default")
            default_route = route_cmd.read()
        finally:
            route_cmd.close()
        my_interface = default_route.split()[4]
        try:
            socket.if_nametoindex(my_interface)  # test if the interface exists.
        except OSError:
            self.fail("Interface Name Error: {}".format(my_interface))
        delay = await ping3.ping(DEST_DOMAIN, interface=my_interface)
        self.assertIsInstance(delay, float)

    @unittest.skipUnless(sys.platform == "linux", "Linux only")
    @pytest.mark.anyio
    async def test_verbose_ping_interface(self):
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            try:
                route_cmd = os.popen("ip -o -4 route show to default")
                default_route = route_cmd.read()
            finally:
                route_cmd.close()
            my_interface = default_route.split()[4]
            try:
                socket.if_nametoindex(my_interface)  # test if the interface exists.
            except OSError:
                self.fail("Interface Name Error: {}".format(my_interface))
            await ping3.verbose_ping(DEST_DOMAIN, interface=my_interface)
            self.assertRegex(fake_out.getvalue(), r".*[0-9]+ms.*")

    @pytest.mark.anyio
    async def test_ping_src_addr(self):
        my_ip = socket.gethostbyname(socket.gethostname())
        if my_ip in ("127.0.0.1", "127.0.1.1"):  # This may caused by /etc/hosts settings.
            dest_addr = my_ip  # only localhost can send and receive from 127.0.0.1 (or 127.0.1.1 on Ubuntu).
        else:
            dest_addr = DEST_DOMAIN
        delay = await ping3.ping(dest_addr, src_addr=my_ip)
        self.assertIsInstance(delay, float)

    @pytest.mark.anyio
    async def test_verbose_ping_src_addr(self):
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            my_ip = socket.gethostbyname(socket.gethostname())
            if my_ip in ("127.0.0.1", "127.0.1.1"):  # This may caused by /etc/hosts settings.
                dest_addr = my_ip  # only localhost can send and receive from 127.0.0.1 (or 127.0.1.1 on Ubuntu).
            else:
                dest_addr = DEST_DOMAIN
            await ping3.verbose_ping(dest_addr, src_addr=my_ip)
            self.assertRegex(fake_out.getvalue(), r".*[0-9]+ms.*")

    @pytest.mark.anyio
    @unittest.skipIf(sys.platform.startswith("win"), "Linux and macOS Only")
    async def test_ping_ttl(self):
        ping3.EXCEPTIONS = False
        delay = await ping3.ping(DEST_DOMAIN, ttl=1)
        self.assertIn(delay, (None, False))  # When TTL expired, some routers report nothing.

    @pytest.mark.anyio
    async def test_ping_ttl_exception(self):
        with patch("ping3.EXCEPTIONS", True):
            with self.assertRaises((ping3.errors.TimeToLiveExpired, ping3.errors.Timeout)):  # When TTL expired, some routers report nothing.
                await ping3.ping(DEST_DOMAIN, ttl=1)

    @unittest.skipIf(sys.platform.startswith("win"), "Linux and macOS Only")
    @pytest.mark.anyio
    async def test_verbose_ping_ttl(self):
        ping3.EXCEPTIONS = False
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            await ping3.verbose_ping(DEST_DOMAIN, ttl=1)
            self.assertNotRegex(fake_out.getvalue(), r".*[0-9]+ms.*")

    @unittest.skipIf(sys.platform.startswith("win"), "Linux and macOS Only")
    @pytest.mark.anyio
    async def test_verbose_ping_ttl_exception(self):
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            with self.assertRaises((ping3.errors.TimeToLiveExpired, ping3.errors.Timeout)):  # When TTL expired, some routers report nothing.
                await ping3.verbose_ping(DEST_DOMAIN, ttl=1)

    @pytest.mark.anyio
    async def test_verbose_ping_count(self):
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            await ping3.verbose_ping(DEST_DOMAIN, count=1)
            self.assertEqual(fake_out.getvalue().count("\n"), 1)

    @pytest.mark.anyio
    async def test_verbose_ping_interval(self):
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            delay = ping3.ping(DEST_DOMAIN)
            self.assertTrue(0 < delay < 0.75)  # If interval does not work, the total delay should be < 3s (4 * 0.75s)
            start_time = time.time()
            await ping3.verbose_ping(DEST_DOMAIN, interval=1)  # If interval does work, the total delay should be > 3s (3 * 1s)
            end_time = time.time()
            self.assertTrue((end_time - start_time) >= 3)  # time_expect = (count - 1) * interval
            self.assertNotIn("Timeout", fake_out.getvalue())  # Ensure no timeout

    @pytest.mark.anyio
    async def test_DEBUG(self):
        with patch("ping3.DEBUG", True), patch("sys.stderr", new=io.StringIO()):
            delay = await ping3.ping(DEST_DOMAIN)

