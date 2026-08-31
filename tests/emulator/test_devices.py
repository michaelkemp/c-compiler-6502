from c6502.emulator.devices import ConsoleDevice


def test_writing_output_register_accumulates_bytes():
    console = ConsoleDevice()
    console.write8(0, ord("H"))
    console.write8(0, ord("i"))
    assert console.output_text == "Hi"


def test_output_register_reads_back_as_zero():
    console = ConsoleDevice()
    console.write8(0, ord("X"))
    assert console.read8(0) == 0


def test_input_register_reads_zero_when_nothing_queued():
    console = ConsoleDevice()
    assert console.read8(1) == 0


def test_feed_input_then_read_in_order():
    console = ConsoleDevice()
    console.feed_input("ab")
    assert console.read8(1) == ord("a")
    assert console.read8(1) == ord("b")
    assert console.read8(1) == 0  # queue drained


def test_writes_to_input_or_other_offsets_are_ignored():
    console = ConsoleDevice()
    console.write8(1, 0x41)  # should not queue anything or raise
    console.write8(99, 0x41)
    assert console.read8(1) == 0
