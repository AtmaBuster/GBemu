import struct, random

OPCODES = {
	0x00 : (0, 1, 'nop'),
	0x01 : (2, 3, 'ld bc, ${val:0>4X}'),
	0x04 : (0, 1, 'inc b'),
	0x05 : (0, 1, 'dec b'),
	0x06 : (1, 8, 'ld b, ${val:0>2X}'),
	0x0C : (0, 1, 'inc c'),
	0x0D : (0, 1, 'dec c'),
	0x0E : (1, 8, 'ld c, ${val:0>2X}'),
	0x11 : (2, 3, 'ld de, ${val:0>4X}'),
	0x13 : (0, 2, 'inc de'),
	0x15 : (0, 1, 'dec d'),
	0x16 : (1, 2, 'ld d, ${val:0>2X}'),
	0x17 : (0, 1, 'rla'),
	0x18 : (1, 2, 'jr ${rel:0>4X}'),
	0x1A : (0, 2, 'ld a, [de]'),
	0x1D : (0, 1, 'dec e'),
	0x1E : (1, 2, 'ld e, ${val:0>2X}'),
	0x20 : (1, 2, 'jr nz, ${rel:0>4X}'),
	0x21 : (2, 3, 'ld hl, ${val:0>4X}'),
	0x22 : (0, 2, 'ldi [hl], a'),
	0x23 : (0, 2, 'inc hl'),
	0x24 : (0, 1, 'inc h'),
	0x28 : (1, 2, 'jr z, ${rel:0>4X}'),
	0x2E : (1, 2, 'ld l, ${val:0>2X}'),
	0x31 : (2, 3, 'ld sp, ${val:0>4X}'),
	0x32 : (0, 2, 'ldd [hl], a'),
	0x3D : (0, 1, 'dec a'),
	0x3E : (1, 2, 'ld a, ${val:0>2X}'),
	0x4F : (0, 1, 'ld c, a'),
	0x57 : (0, 1, 'ld d, a'),
	0x67 : (0, 1, 'ld h, a'),
	0x77 : (0, 2, 'ld [hl], a'),
	0x78 : (0, 1, 'ld a, b'),
	0x7B : (0, 1, 'ld a, e'),
	0x7C : (0, 1, 'ld a, h'),
	0x7D : (0, 1, 'ld a, l'),
	0x86 : (0, 2, 'add [hl]'),
	0x90 : (0, 1, 'sub b'),
	0xC1 : (0, 3, 'pop bc'),
	0xC5 : (0, 4, 'push bc'),
	0xC9 : (0, 2, 'ret'),
	0xCB : (1, 2, 'CB'),
	0xCD : (2, 3, 'call ${val:0>4X}'),
	0xAF : (0, 1, 'xor a'),
	0xBE : (0, 2, 'cp [hl]'),
	0xE0 : (1, 3, 'ldh [$FF{val:0>2X}], a'),
	0xF0 : (1, 3, 'ldh a, [$FF{val:0>2X}]'),
	0xE2 : (0, 2, 'ldh [c], a'),
	0xEA : (2, 4, 'ld [${val:0>4X}], a'),
	0xFE : (1, 2, 'cp ${val:0>2X}'),
}

HEADER_LOGO = \
	b'\xCE\xED\x66\x66\xCC\x0D\x00\x0B' + \
	b'\x03\x73\x00\x83\x00\x0C\x00\x0D' + \
	b'\x00\x08\x11\x1F\x88\x89\x00\x0E' + \
	b'\xDC\xCC\x6E\xE6\xDD\xDD\xD9\x99' + \
	b'\xBB\xBB\x67\x63\x6E\x0E\xEC\xCC' + \
	b'\xDD\xDC\x99\x9F\xBB\xB9\x33\x3E'

CART_DATA = {
	0x00: (None, 'ROM ONLY'),
	0x01: ('MBC1', 'MBC1'),
	0x02: ('MBC1', 'MBC1+RAM'),
	0x03: ('MBC1', 'MBC1+RAM+BATTERY'),
	0x05: ('MBC2', 'MBC2'),
	0x06: ('MBC2', 'MBC2+BATTERY'),
	0x08: (None, 'ROM+RAM'),
	0x09: (None, 'ROM+RAM+BATTERY'),
	0x0B: ('MMM01', 'MMM01'),
	0x0C: ('MMM01', 'MMM01+RAM'),
	0x0D: ('MMM01', 'MMM01+RAM+BATTERY'),
	0x0F: ('MBC3', 'MBC3+TIMER+BATTERY'),
	0x10: ('MBC3', 'MBC3+TIMER+RAM+BATTERY'),
	0x11: ('MBC3', 'MBC3'),
	0x12: ('MBC3', 'MBC3+RAM'),
	0x13: ('MBC3', 'MBC3+RAM+BATTERY'),
	0x19: ('MBC5', 'MBC5'),
	0x1A: ('MBC5', 'MBC5+RAM'),
	0x1B: ('MBC5', 'MBC5+RAM+BATTERY'),
	0x1C: ('MBC5', 'MBC5+RUMBLE'),
	0x1D: ('MBC5', 'MBC5+RUMBLE+RAM'),
	0x1E: ('MBC5', 'MBC5+RUMBLE+RAM+BATTERY'),
	0x20: ('MBC6', 'MBC6'),
	0x22: ('MBC7', 'MBC7+SENSOR+RUMBLE+RAM+BATTERY'),
	0xFC: (None, 'POCKET CAMERA'),
	0xFD: (None, 'BANTAI TAMA5'),
	0xFE: ('HuC3', 'HuC3'),
	0xFF: ('HuC1', 'HuC1+RAM+BATTERY'),
}

inrng = lambda x, a, b: a <= x and x <= b

class MBC:
	def __init__(self, ver):
		self.ver = ver

		self.rom_bank = 1
		self.ram_bank = 0
		self.ram_loaded = False

	def write_at(self, adr, val):
		if inrng(adr, 0x0000, 0xFFFF):
			pass

R_HEX   = 0
R_INT   = 1
R_UINT  = 2
R_ASCII = 3
class ROM:
	def __init__(self, f_rom, f_sav=None):
		self.bus = None

		if isinstance(f_rom, str):
			self.f_rom = open(f_rom, 'rb')
		else:
			self.f_rom = f_rom
		if f_sav is None:
			self.f_sav = None
		elif isinstance(f_sav, str):
			self.f_sav = open(f_sav, 'rb')
		else:
			self.f_sav = f_sav
		self.valid_rom = 0
		# get some header info
		self.header = {}
		self.sk(0x104)
		self.header['logo'] = self.f_rom.read(0x30)
		if self.header['logo'] != HEADER_LOGO:
			self.valid_rom = 1
		self.header['title'] = self.f_rom.read(0x10)
		self.header['manufacturer'] = self.header['title'][0xB:0xF]
		self.header['cgb'] = self.header['title'][0xF]
		self.header['licensee'] = self.rh(R_HEX)
		self.header['sgb'] = self.rb(R_HEX)
		cart_data_byte = self.rb(R_UINT)
		self.header['cartridge'] = CART_DATA.get(cart_data_byte, f'ERR ${cart_data_byte:0>2X}')
		if isinstance(self.header['cartridge'], str):
			self.valid_rom = 2
		rom_size_byte = self.rb(R_UINT)
		if rom_size_byte <= 8:
			bank_ct = 2 << rom_size_byte
			if bank_ct < 64:
				rom_size = f'{bank_ct*16} KB'
			else:
				rom_size = f'{bank_ct//64} MB'
			self.header['romsize'] = (bank_ct, rom_size) # num banks
		else:
			self.header['romsize'] = f'ERR ${rom_size_byte:0>2X}'
			self.valid_rom = 3
		ram_size_byte = self.rb(R_UINT)
		if ram_size_byte <= 5 and ram_size_byte != 1:
			bank_ct = [0, None, 1, 4, 16, 8][ram_size_byte]
			ram_size = ['0 B', None, '8 KB', '32 KB', '128 KB', '64 KB'][ram_size_byte]
			self.header['ramsize'] = (bank_ct, ram_size)
		else:
			self.header['ramsize'] = f'ERR ${ram_size_byte:0>2X}'
			self.valid_rom = 4
		self.header['destination'] = self.rb(R_UINT)
		self.header['old_licensee'] = self.rb(R_HEX)
		self.header['version'] = self.rb(R_HEX)
		self.header['header_checksum'] = self.rb(R_UINT)
		self.header['global_checksum'] = self.rhb(R_UINT)
		# verify header checksum
		self.sk(0x134)
		chk = 0
		for _ in range(0x14D - 0x134):
			chk = (chk - self.rb(R_UINT) - 1) % 0x100
		if chk != self.header['header_checksum']:
			self.valid_rom = 5
		# verify global checksum
		self.sk(0)
		cur_adr = 0
		chk = 0
		while True:
			cur_h = self.f_rom.read(1)
			if cur_h == b'': break
			if cur_adr != 0x14E and cur_adr != 0x14F:
				chk = (chk + struct.unpack('B', cur_h)[0]) & 0xFFFF
			cur_adr += 1
		if chk != self.header['global_checksum']:
			self.valid_rom = 6

		if self.valid_rom > 0:
			self.mbc = MBC(None)
		else:
			self.mbc = MBC(self.header['cartridge'][0])

	def sk(self, arg1, arg2=None):
		if arg2 is None:
			if isinstance(arg1, str):
				b, a = arg1.split(':')
				self.sk(int(b, 16), int(a, 16))
			else:
				self.f_rom.seek(arg1)
		else:
			adr = arg2
			if arg1 != 0:
				arg2 -= 0x4000
			adr += arg1 * 0x4000
			self.f_rom.seek(adr)

	def rb(self, mode=R_UINT):
		b = self.f_rom.read(1)
		if mode == R_HEX:
			return b
		if mode == R_UINT:
			return b[0]
		if mode == R_INT:
			x = b[0]
			if x > 0x7F:
				x = 0x100 - x
			return x
		if mode == R_ASCII:
			return b.decode('ascii')
		print(f'ERROR READ MODE {mode}')

	def rh(self, mode=R_UINT):
		h = self.f_rom.read(2)
		if mode == R_HEX:
			return h
		if mode == R_UINT:
			return struct.unpack('<H', h)[0]
		if mode == R_INT:
			return struct.unpack('<h', h)[0]
		if mode == R_ASCII:
			return h.decode('ascii')
		print(f'ERROR READ MODE {mode}')

	def rhb(self, mode=R_UINT):
		h = self.f_rom.read(2)
		if mode == R_HEX:
			return h
		if mode == R_UINT:
			return struct.unpack('>H', h)[0]
		if mode == R_INT:
			return struct.unpack('>h', h)[0]
		if mode == R_ASCII:
			return h.decode('ascii')
		print(f'ERROR READ MODE {mode}')

	def write_at(self, adr, val):
		# writes <val> to the ROM (MBC) or RAM at 16-bit address <adr>
		self.mbc.write_at(adr, val)
		if inrng(adr, 0x0000, 0x9FFF):
			pass
		elif inrng(adr, 0xA000, 0xBFFF):
			if self.mbc.ram_loaded:
				pass # TODO
			else:
				pass
		elif inrng(adr, 0xC000, 0xFFFF):
			pass

	def read_at(self, adr):
		# reads the ROM at 16-bit address <adr>
		if inrng(adr, 0x0000, 0x3FFF):
			# bank-0
			self.sk(adr)
			return self.rb()
		elif inrng(adr, 0x4000, 0x7FFF):
			# bank-n
			self.sk(self.mbc.bank, adr)
			return self.rb()
		elif inrng(adr, 0x8000, 0x9FFF):
			return None
		elif inrng(adr, 0xA000, 0xBFFF):
			if self.mbc.ram_loaded:
				return 0x00 # TODO
			else:
				return 0xFF
		elif inrng(adr, 0xC000, 0xFFFF):
			return None

class VRAM:
	def __init__(self):
		self.bus = None

		# ~ self.tile0 = [0x00] * 0x800
		# ~ self.tile1 = [0x00] * 0x800
		# ~ self.tile2 = [0x00] * 0x800
		# ~ self.bgmap0 = [0x00] * 0x400
		# ~ self.bgmap1 = [0x00] * 0x400

		self.tile0 = [random.randint(0, 255) for _ in range(0x800)]
		self.tile1 = [random.randint(0, 255) for _ in range(0x800)]
		self.tile2 = [random.randint(0, 255) for _ in range(0x800)]
		self.bgmap0 = [random.randint(0, 255) for _ in range(0x400)]
		self.bgmap1 = [random.randint(0, 255) for _ in range(0x400)]

		self.vblank = True

	def write_at(self, adr, val):
		if inrng(adr, 0x0000, 0x7FFF):
			pass
		elif inrng(adr, 0x8000, 0x87FF):
			self.tile0[adr - 0x8000] = val
		elif inrng(adr, 0x8800, 0x8FFF):
			self.tile1[adr - 0x8800] = val
		elif inrng(adr, 0x9000, 0x97FF):
			self.tile2[adr - 0x9000] = val
		elif inrng(adr, 0x9800, 0x9BFF):
			self.bgmap0[adr - 0x9800] = val
		elif inrng(adr, 0x9C00, 0x9FFF):
			self.bgmap1[adr - 0x9C00] = val
		elif inrng(adr, 0xA000, 0xFFFF):
			pass

	def read_at(self, adr):
		if inrng(adr, 0x0000, 0x7FFF):
			return None
		elif inrng(adr, 0x8000, 0x87FF):
			if self.vblank:
				return self.tile0[adr - 0x8000]
			else:
				return 0xFF
		elif inrng(adr, 0x8800, 0x8FFF):
			if self.vblank:
				return self.tile1[adr - 0x8800]
			else:
				return 0xFF
		elif inrng(adr, 0x9000, 0x97FF):
			if self.vblank:
				return self.tile2[adr - 0x9000]
			else:
				return 0xFF
		elif inrng(adr, 0x9800, 0x9BFF):
			if self.vblank:
				return self.bgmap0[adr - 0x9800]
			else:
				return 0xFF
		elif inrng(adr, 0x9C00, 0x9FFF):
			if self.vblank:
				return self.bgmap1[adr - 0x9C00]
			else:
				return 0xFF
		elif inrng(adr, 0xA000, 0xFFFF):
			pass

	def set_vblank(self, state):
		self.vblank = True


class IOReg:
	def __init__(self):
		self.bus = None

		self.data = [0x00] * 0x80

	def write_at(self, adr, val):
		if inrng(adr, 0x0000, 0xFEFF):
			pass
		elif inrng(adr, 0xFF00, 0xFF7F):
			self.data[adr - 0xFF00] = val
		elif inrng(adr, 0xFF80, 0xFFFF):
			pass

	def read_at(self, adr):
		if inrng(adr, 0x0000, 0xFEFF):
			return None
		elif inrng(adr, 0xFF00, 0xFF7F):
			return self.data[adr - 0xFF00]
		elif inrng(adr, 0xFF80, 0xFFFF):
			return None

class HRAM:
	def __init__(self):
		self.bus = None

		self.hram = [0x00] * 0x7F

	def write_at(self, adr, val):
		if inrng(adr, 0x0000, 0xFF7F):
			pass
		elif inrng(adr, 0xFF80, 0xFFFE):
			self.hram[adr - 0xFF80] = val
		elif inrng(adr, 0xFFFF, 0xFFFF):
			pass

	def read_at(self, adr):
		if inrng(adr, 0x0000, 0xFF7F):
			return None
		elif inrng(adr, 0xFF80, 0xFFFE):
			return self.hram[adr - 0xFF80]
		elif inrng(adr, 0xFFFF, 0xFFFF):
			return None

class WRAM:
	def __init__(self):
		self.bus = None

		self.wram0 = [0x00] * 0x1000
		self.wram1 = [0x00] * 0x1000

	def write_at(self, adr, val):
		if inrng(adr, 0x0000, 0xBFFF):
			pass
		elif inrng(adr, 0xC000, 0xCFFF):
			self.wram0[adr - 0xC000] = val
		elif inrng(adr, 0xD000, 0xDFFF):
			self.wram1[adr - 0xD000] = val # TODO
		elif inrng(adr, 0xE000, 0xEFFF):
			self.wram0[adr - 0xE000] = val
		elif inrng(adr, 0xF000, 0xFDFF):
			self.wram1[adr - 0xF000] = val # TODO
		elif inrng(adr, 0xFE00, 0xFFFF):
			pass

	def read_at(self, adr):
		if inrng(adr, 0x0000, 0xBFFF):
			return None
		elif inrng(adr, 0xC000, 0xCFFF):
			return self.wram0[adr - 0xC000]
		elif inrng(adr, 0xD000, 0xDFFF):
			return self.wram1[adr - 0xD000] # TODO
		elif inrng(adr, 0xE000, 0xEFFF):
			return self.wram0[adr - 0xE000]
		elif inrng(adr, 0xF000, 0xFDFF):
			return self.wram1[adr - 0xF000] # TODO
		elif inrng(adr, 0xFE00, 0xFFFF):
			return None

USE_BOOTROM = True
class CPU:
	def __init__(self):
		self.bus = None

		if USE_BOOTROM:
			self.reg_a = random.randint(0x00, 0xFF)
			self.reg_f = random.randint(0x00, 0xFF)
			self.reg_b = random.randint(0x00, 0xFF)
			self.reg_c = random.randint(0x00, 0xFF)
			self.reg_d = random.randint(0x00, 0xFF)
			self.reg_e = random.randint(0x00, 0xFF)
			self.reg_h = random.randint(0x00, 0xFF)
			self.reg_l = random.randint(0x00, 0xFF)
			self.reg_sp = random.randint(0x00, 0xFFFF)
			self.reg_pc = 0
		else:
			self.reg_a = 0x11
			self.reg_f = 0x80
			self.reg_b = 0xDB
			self.reg_c = 0x00
			self.reg_d = 0x00
			self.reg_e = 0x08
			self.reg_h = 0x00
			self.reg_l = 0x7C
			self.reg_sp = 0xFFFE
			self.reg_pc = 0x00FE

	def stack_push(self, val):
		self.reg_sp = (self.reg_sp - 1) % 0x10000
		self.bus.write_at(self.reg_sp, val >> 8)
		self.reg_sp = (self.reg_sp - 1) % 0x10000
		self.bus.write_at(self.reg_sp, val & 0xFF)

	def stack_pop(self):
		val = self.bus.read_at(self.reg_sp)
		self.reg_sp = (self.reg_sp + 1) % 0x10000
		val |= self.bus.read_at(self.reg_sp) << 8
		self.reg_sp = (self.reg_sp + 1) % 0x10000
		return val

	@property
	def reg_bc(self):
		return (self.reg_b << 8) | self.reg_c
	@reg_bc.setter
	def reg_bc(self, val):
		val_hi = val >> 8
		val_lo = val & 0xFF
		self.reg_b = val_hi
		self.reg_c = val_lo

	@property
	def reg_de(self):
		return (self.reg_d << 8) | self.reg_e
	@reg_de.setter
	def reg_de(self, val):
		val_hi = val >> 8
		val_lo = val & 0xFF
		self.reg_d = val_hi
		self.reg_e = val_lo

	@property
	def reg_hl(self):
		return (self.reg_h << 8) | self.reg_l
	@reg_hl.setter
	def reg_hl(self, val):
		val_hi = val >> 8
		val_lo = val & 0xFF
		self.reg_h = val_hi
		self.reg_l = val_lo

	@property
	def reg_af(self):
		return (self.reg_a << 8) | self.reg_f

	@property
	def flg_z(self):
		return bool(self.reg_f & 0x80)
	@flg_z.setter
	def flg_z(self, val):
		self.reg_f |= 0x80
		if not val:
			self.reg_f ^= 0x80

	@property
	def flg_n(self):
		return bool(self.reg_f & 0x40)
	@flg_n.setter
	def flg_n(self, val):
		self.reg_f |= 0x40
		if not val:
			self.reg_f ^= 0x40

	@property
	def flg_h(self):
		return bool(self.reg_f & 0x20)
	@flg_h.setter
	def flg_h(self, val):
		self.reg_f |= 0x20
		if not val:
			self.reg_f ^= 0x20

	@property
	def flg_c(self):
		return bool(self.reg_f & 0x10)
	@flg_c.setter
	def flg_c(self, val):
		self.reg_f |= 0x10
		if not val:
			self.reg_f ^= 0x10

	def write_at(self, adr, val):
		pass

	def read_at(self, adr):
		return None

	def run_opcode(self, opcode, arg):
		if opcode == 0x00:   # nop
			pass
		elif opcode == 0x01: # ld bc, arg
			self.reg_bc = arg
		elif opcode == 0x04: # inc b
			self.reg_b = (self.reg_b + 1) % 0x100
			self.flg_z = self.reg_b == 0
			self.flg_n = False
			self.flg_h = (self.reg_b & 0xF) == 0x0
		elif opcode == 0x05: # dec b
			self.reg_b = (self.reg_b - 1) % 0x100
			self.flg_z = self.reg_b == 0
			self.flg_n = True
			self.flg_h = (self.reg_b & 0xF) == 0xF
		elif opcode == 0x06: # ld b, arg
			self.reg_b = arg
		elif opcode == 0x0C: # inc c
			self.reg_c = (self.reg_c + 1) % 0x100
			self.flg_z = self.reg_c == 0
			self.flg_n = False
			self.flg_h = (self.reg_c & 0xF) == 0x0
		elif opcode == 0x0D: # dec c
			self.reg_c = (self.reg_c - 1) % 0x100
			self.flg_z = self.reg_c == 0
			self.flg_n = True
			self.flg_h = (self.reg_c & 0xF) == 0xF
		elif opcode == 0x0E: # ld c, arg
			self.reg_c = arg
		elif opcode == 0x11: # ld de, arg
			self.reg_de = arg
		elif opcode == 0x13: # inc de
			self.reg_de = (self.reg_de + 1) % 0x10000
		elif opcode == 0x15: # dec d
			self.reg_d = (self.reg_d - 1) % 0x100
			self.flg_z = self.reg_d == 0
			self.flg_n = True
			self.flg_h = (self.reg_d & 0xF) == 0xF
		elif opcode == 0x16: # ld d, arg
			self.reg_d = arg
		elif opcode == 0x17: # rla
			new_c = self.reg_a & 0x80
			self.reg_a <<= 1
			self.reg_a &= 0xFF
			if self.flg_c:
				self.reg_a |= 0x1
			self.flg_c = bool(new_c)
			self.flg_z = self.reg_a == 0
			self.flg_n = False
			self.flg_h = False
		elif opcode == 0x18: # jr pc + arg
			if arg > 0x7F:
				arg = arg - 0x100
			self.reg_pc += arg
		elif opcode == 0x1A: # ld a, [de]
			self.reg_a = self.bus.read_at(self.reg_de)
		elif opcode == 0x1D: # dec e
			self.reg_e = (self.reg_e - 1) % 0x100
			self.flg_z = self.reg_e == 0
			self.flg_n = True
			self.flg_h = (self.reg_e & 0xF) == 0xF
		elif opcode == 0x1E: # ld e, arg
			self.reg_e = arg
		elif opcode == 0x20: # jr nz, pc + arg
			if not self.flg_z:
				if arg > 0x7F:
					arg = arg - 0x100
				self.reg_pc += arg
				return 1
		elif opcode == 0x21: # ld hl, arg
			self.reg_hl = arg
		elif opcode == 0x22: # ldi [hl], a
			self.bus.write_at(self.reg_hl, self.reg_a)
			self.reg_hl = (self.reg_hl + 1) % 0x10000
		elif opcode == 0x23: # inc hl
			self.reg_hl = (self.reg_hl + 1) % 0x10000
		elif opcode == 0x24: # inc h
			self.reg_h = (self.reg_h + 1) % 0x100
			self.flg_z = self.reg_h == 0
			self.flg_n = False
			self.flg_h = (self.reg_h & 0xF) == 0x0
		elif opcode == 0x28: # jr z, pc + arg
			if self.flg_z:
				if arg > 0x7F:
					arg = arg - 0x100
				self.reg_pc += arg
				return 1
		elif opcode == 0x2E: # ld l, arg
			self.reg_l = arg
		elif opcode == 0x31: # ld sp, arg
			self.reg_sp = arg
		elif opcode == 0x32: # ldd [hl], a
			self.bus.write_at(self.reg_hl, self.reg_a)
			self.reg_hl = (self.reg_hl - 1) % 0x10000
		elif opcode == 0x3D: # dec a
			self.reg_a = (self.reg_a - 1) % 0x100
			self.flg_z = self.reg_a == 0
			self.flg_n = True
			self.flg_h = (self.reg_a & 0xF) == 0xF
		elif opcode == 0x3E: # ld a, arg
			self.reg_a = arg
		elif opcode == 0x4F: # ld c, a
			self.reg_c = self.reg_a
		elif opcode == 0x57: # ld d, a
			self.reg_d = self.reg_a
		elif opcode == 0x67: # ld h, a
			self.reg_h = self.reg_a
		elif opcode == 0x77: # ld [hl], a
			self.bus.write_at(self.reg_hl, self.reg_a)
		elif opcode == 0x78: # ld a, b
			self.reg_a = self.reg_b
		elif opcode == 0x7B: # ld a, e
			self.reg_a = self.reg_e
		elif opcode == 0x7C: # ld a, h
			self.reg_a = self.reg_h
		elif opcode == 0x7D: # ld a, l
			self.reg_a = self.reg_l
		elif opcode == 0x86: # add [hl]
			val = self.bus.read_at(self.reg_hl)
			self.flg_z = self.reg_a + val == 0x100
			self.flg_n = False
			self.flg_h = (self.reg_a & 0xF) + (val & 0xF) > 0xF
			self.flg_c = self.reg_a + val > 0xFF
			self.reg_a = (self.reg_a + val) % 0x100
		elif opcode == 0x90: # sub b
			self.flg_z = self.reg_a == self.reg_b
			self.flg_n = True
			self.flg_h = (self.reg_a & 0xF) < (self.reg_b & 0xF)
			self.flg_c = self.reg_a < self.reg_b
			self.reg_a = (self.reg_a - self.reg_b) % 0x100
		elif opcode == 0xBE: # cp [hl]
			val = self.bus.read_at(self.reg_hl)
			self.flg_z = self.reg_a == val
			self.flg_n = True
			self.flg_h = (self.reg_a & 0xF) < (val & 0xF)
			self.flg_c = self.reg_a < val
		elif opcode == 0xC1: # pop bc
			self.reg_bc = self.stack_pop()
		elif opcode == 0xC5: # push bc
			self.stack_push(self.reg_bc)
		elif opcode == 0xC9: # ret
			self.reg_pc = self.stack_pop()
		elif opcode == 0xCD: # call arg
			self.stack_push(self.reg_pc)
			self.reg_pc = arg
		elif opcode == 0xAF: # xor a
			self.reg_a = 0
			self.flg_z = False
			self.flg_n = False
			self.flg_h = False
			self.flg_c = False
		elif opcode == 0xE0: # ldh [$FF00+arg], a
			adr = 0xFF00 + arg
			self.bus.write_at(adr, self.reg_a)
		elif opcode == 0xE2: # ldh [c], a
			adr = 0xFF00 + self.reg_c
			self.bus.write_at(adr, self.reg_a)
		elif opcode == 0xEA: # ld [arg], a
			self.bus.write_at(arg, self.reg_a)
		elif opcode == 0xF0: # ldh a, [$FF00+arg]
			adr = 0xFF00 + arg
			self.reg_a = self.bus.read_at(adr)
		elif opcode == 0xFE: # cp arg
			self.flg_z = self.reg_a == arg
			self.flg_n = True
			self.flg_h = (self.reg_a & 0xF) < (arg & 0xF)
			self.flg_c = self.reg_a < arg
		else:
			raise Exception(f'ERROR: unknown opcode :: ${opcode:0>2X}')
		return 0

	def run_opcode_cb(self, opcode):
		if opcode == 0x11:   # rl c
			new_c = self.reg_c & 0x80
			self.reg_c <<= 1
			self.reg_c &= 0xFF
			if self.flg_c:
				self.reg_c |= 0x1
			self.flg_c = bool(new_c)
			self.flg_z = self.reg_c == 0
			self.flg_n = False
			self.flg_h = False
			return 'rl c'
		elif opcode == 0x7C: # bit 7, h
			self.flg_z = not bool(self.reg_h & 0x80)
			self.flg_n = False
			self.flg_h = True
			return 'bit 7, h'
		else:
			raise Exception(f'ERROR: unknown $CB opcode :: ${opcode:0>2X}')

class BootROM:
	def __init__(self, bus):
		self.bus = bus
		self.data = open('bootrom.gb', 'rb').read()

class Bus:
	def __init__(self):
		self.cpu = None
		self.rom = None
		self.wram = None
		self.hram = None
		self.vram = None
		self.ioreg = None

		self.bootrom = BootROM(self)
		self.bootrom_loaded = True

		self.frame_cycles = 0
		self.hit_frame = False

	def pass_cycle(self):
		self.frame_cycles += 1
		if self.frame_cycles == 17476:
			# next frame
			self.frame_cycles = 0
			self.hit_frame = True

		scanline = int(self.frame_cycles / 113.48052)
		self.ioreg.write_at(0xFF44, scanline)

	def pass_cycles(self, n):
		for _ in range(n):
			self.pass_cycle()

	def link_device(self, dev, obj):
		if dev == 'CPU':
			self.cpu = obj
		elif dev == 'ROM':
			self.rom = obj
		elif dev == 'WRAM':
			self.wram = obj
		elif dev == 'HRAM':
			self.hram = obj
		elif dev == 'VRAM':
			self.vram = obj
		elif dev == 'IO':
			self.ioreg = obj
		else:
			raise Exception(f'Unknown device "{dev}"')
		obj.bus = self

	def get_devices(self):
		dev = []
		if not self.cpu   is None: dev.append(self.cpu)
		if not self.rom   is None: dev.append(self.rom)
		if not self.wram  is None: dev.append(self.wram)
		if not self.hram  is None: dev.append(self.hram)
		if not self.vram  is None: dev.append(self.vram)
		if not self.ioreg is None: dev.append(self.ioreg)
		return dev

	def write_at(self, adr, val):
		# BOOTROM DISABLE ADDR
		if adr == 0xFF50 and val != 1:
			self.bootrom = None
			self.bootrom_loaded = False
		for dev in self.get_devices():
			dev.write_at(adr, val)

	def read_at(self, adr):
		if self.bootrom_loaded and adr < 0x100:
			return self.bootrom.data[adr]
		b = None
		for dev in self.get_devices():
			new_b = dev.read_at(adr)
			if new_b is None: continue
			if not b is None:
				# bus contention
				b = random.randint(0, 255)
			else:
				b = new_b
		if b is None:
			# open bus
			if adr >= 0x8000 or not self.rom is None:
				print(f'open bus @ ${adr:0>4X}')
			b = 0xFF
		return b

	def read_at_pc(self):
		b = self.read_at(self.cpu.reg_pc)
		self.cpu.reg_pc += 1
		return b

	def do_instruction(self):
		if self.cpu is None: return
		raw = f'${self.cpu.reg_pc:0>4X}  '
		opcode = self.read_at_pc()
		raw += f'{opcode:0>2X}'
		if not opcode in OPCODES.keys():
			print(f'Unknown opcode ${opcode:0>2X} at ${self.cpu.reg_pc-1:0>4X}')
			return 'INVALID OPCODE'

		narg, cycles, disasm = OPCODES[opcode]
		if narg == 0:
			arg = None
			raw += f'      '
		elif narg == 1:
			arg = self.read_at_pc()
			raw += f' {arg:0>2X}   '
		elif narg == 2:
			arg = self.read_at_pc()
			raw += f' {arg:0>2X} '
			arg2 = self.read_at_pc()
			raw += f'{arg2:0>2X}'
			arg |= arg2 << 8
		if opcode == 0xCB:
			# special
			dis_str = self.cpu.run_opcode_cb(arg)
			if arg & 0b111 == 0b110:
				cycles += 1
		else:
			dis_dict = {
				'val': arg,
				'rel': self.cpu.reg_pc + signb(arg),
			}
			# ~ print(disasm)
			# ~ print(dis_dict)
			dis_str = disasm.format(**dis_dict)
			ext_cycles = self.cpu.run_opcode(opcode, arg)
			cycles += ext_cycles

		self.pass_cycles(cycles)

		return raw + '   |   ' + dis_str

def signb(i):
	if i is None: return 0
	if i < 0x80:
		return i
	return i - 0x100

class Emu:
	def __init__(self):
		self.bus = Bus()

		self.cpu = CPU()
		self.bus.link_device('CPU', self.cpu)
		self.wram = WRAM()
		self.bus.link_device('WRAM', self.wram)
		self.hram = HRAM()
		self.bus.link_device('HRAM', self.hram)
		self.vram = VRAM()
		self.bus.link_device('VRAM', self.vram)
		self.ioreg = IOReg()
		self.bus.link_device('IO', self.ioreg)

	def load_rom(self, rom):
		self.rom = rom
		self.bus.link_device('ROM', rom)

if __name__ == '__main__':
	pass
