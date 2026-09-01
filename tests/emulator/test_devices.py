from c6502.emulator.devices import AciaDevice


def test_data_register_transmit_accumulates_output():
    acia = AciaDevice()
    acia.write8(0, ord("H"))
    acia.write8(0, ord("i"))
    assert acia.output_text == "Hi"


def test_on_transmit_callback_fires_for_each_byte():
    seen = []
    acia = AciaDevice(on_transmit=seen.append)
    acia.write8(0, 0x41)
    acia.write8(0, 0x42)
    assert seen == [0x41, 0x42]


def test_status_tdre_always_set_no_transmit_delay_modeled():
    acia = AciaDevice()
    assert acia.read8(1) & 0x10  # TDRE


def test_status_rdrf_reflects_queued_input():
    acia = AciaDevice()
    assert not (acia.read8(1) & 0x08)  # RDRF clear, nothing queued
    acia.feed_input("a")
    assert acia.read8(1) & 0x08  # RDRF set


def test_reading_data_register_pops_input_and_clears_rdrf():
    acia = AciaDevice()
    acia.feed_input("ab")
    assert acia.read8(0) == ord("a")
    assert acia.read8(1) & 0x08  # still one byte queued
    assert acia.read8(0) == ord("b")
    assert not (acia.read8(1) & 0x08)  # queue drained, RDRF clear


def test_data_register_reads_zero_when_nothing_queued():
    acia = AciaDevice()
    assert acia.read8(0) == 0


def test_command_register_round_trips():
    acia = AciaDevice()
    acia.write8(2, 0x09)
    assert acia.read8(2) == 0x09


def test_control_register_round_trips_but_has_no_behavior():
    acia = AciaDevice()
    acia.write8(3, 0xFF)
    assert acia.read8(3) == 0xFF


def test_irq_asserted_requires_dtr_ready_and_rdrf():
    acia = AciaDevice()
    acia.write8(2, 0x01)  # DTR=1, receiver IRQ enabled (bit1=0), no input yet
    assert not acia.irq_asserted
    acia.feed_input("x")
    assert acia.irq_asserted


def test_irq_asserted_false_when_receiver_irq_disabled():
    acia = AciaDevice()
    acia.write8(2, 0x03)  # DTR=1, receiver IRQ disabled (bit1=1)
    acia.feed_input("x")
    assert not acia.irq_asserted


def test_irq_asserted_false_when_dtr_clear():
    acia = AciaDevice()
    acia.write8(2, 0x00)  # DTR=0 -- "enables all selected interrupts" bit is off
    acia.feed_input("x")
    assert not acia.irq_asserted


def test_status_irq_bit_reflects_irq_asserted():
    acia = AciaDevice()
    acia.write8(2, 0x01)
    acia.feed_input("x")
    assert acia.read8(1) & 0x80  # IRQ bit


def test_writing_status_register_triggers_program_reset():
    acia = AciaDevice()
    acia.write8(2, 0x0F)  # set DTR, receiver-IRQ-disable, and RTS bits
    acia.write8(1, 0x00)  # any write to status -- value is ignored
    assert acia.command & 0x0F == 0  # program reset cleared bits 0-3
