import pygame
import emu

BREAKPOINT = -1

class Font:
	def __init__(self):
		self.surf = pygame.image.load('ascii_font.png')
		self.surf.set_colorkey(pygame.Color(255, 255, 255))

	def render(self, txt):
		lins = txt.split('\n')
		w = max([len(x) for x in lins])
		h = len(lins)
		s_out = pygame.Surface((w * 8, h * 8), pygame.SRCALPHA)
		for y,l in enumerate(lins):
			for x,c in enumerate(l):
				s_out.blit(self.surf, (x*8, y*8), self.getc(ord(c)))
		return s_out

	def getc(self, i):
		if i < 0x20 or i > 0x7E:
			i = 0x20
		x = i % 16
		y = i // 16 - 2
		return pygame.Rect((x * 8, y * 8, 8, 8))

'''
Window layout:

Screen                  8, 8 -> 328, 296
Reg Info                336, 8 -> ???, ???

'''

BASE_PAL = (
	pygame.Color(224, 248, 208),
	pygame.Color(136, 192, 112),
	pygame.Color( 52, 104,  86),
	pygame.Color(  8,  24,  32),
)

class Game:
	def __init__(self):
		self.font = Font()

		self.vram_surf = None

		self.win = pygame.display.set_mode((800, 600))

	def do_one_instruction(self):
		try:
			dis_str = self.emu.bus.do_instruction()
		except Exception as e:
			self.running = False
			dis_str = 'UNKNOWN OPCODE'
			raise
		if len(self.last_dis) >= 30:
			self.last_dis.pop(0)
		self.last_dis.append(dis_str)

	def do_n_instructions(self, n):
		for _ in range(n):
			self.do_one_instruction()
			if self.emu.cpu.reg_pc == BREAKPOINT:
				self.running = False
				return

	def do_instructions_until_frame(self):
		while True:
			self.do_one_instruction()
			if self.emu.cpu.reg_pc == BREAKPOINT:
				self.running = False
				return
			if self.emu.bus.hit_frame:
				self.emu.bus.hit_frame = False
				return

	def do_instructions_until_frame_then_stop(self):
		while True:
			self.do_one_instruction()
			if self.emu.cpu.reg_pc == BREAKPOINT:
				self.running = False
				return
			if self.emu.bus.hit_frame:
				self.emu.bus.hit_frame = False
				self.running = False
				return

	def get_tiles_surf(self, which):
		if which == 0:
			lst = self.emu.vram.tile0
		elif which == 1:
			lst = self.emu.vram.tile1
		elif which == 2:
			lst = self.emu.vram.tile2
		s = pygame.Surface((16 * 8, 8 * 8))
		px = pygame.PixelArray(s)
		for til_y in range(8):
			for til_x in range(16):
				til_i = til_y * 16 + til_x
				for px_y in range(8):
					byt0_i = til_i * 16 + px_y * 2
					byt1_i = til_i * 16 + px_y * 2 + 1
					b0 = lst[byt0_i]
					b1 = lst[byt1_i]
					for px_x in range(8):
						c_i = (((b1 >> (7 - px_x)) & 1) << 1) | ((b0 >> (7 - px_x)) & 1)
						px[til_x * 8 + px_x, til_y * 8 + px_y] = BASE_PAL[c_i]
		return s

	def get_bgmap_surf(self, which, tiles):
		def get_tile(i):
			# work on this
			if i < 0x80:
				s = tiles[0]
			else:
				s = tiles[1]
				i -= 0x80
			x = (i % 16) * 8
			y = (i // 16) * 8
			return s.subsurface(pygame.Rect(x, y, 8, 8))
		sout = pygame.Surface((256, 256))
		if which == 0:
			lst = self.emu.vram.bgmap0
		elif which == 1:
			lst = self.emu.vram.bgmap1
		for y in range(32):
			for x in range(32):
				i = y * 32 + x
				t = lst[i]
				sout.blit(get_tile(t), (x * 8, y * 8))
		return sout

	def get_vram(self):
		t0 = self.get_tiles_surf(0)
		t1 = self.get_tiles_surf(1)
		t2 = self.get_tiles_surf(2)
		mp = self.get_bgmap_surf(0, (t0, t1, t2))

		s = pygame.Surface((392, 256))
		s.fill(pygame.Color(248,248,248))
		s.blit(t0, (0, 0))
		s.blit(t1, (0, 64))
		s.blit(t2, (0, 128))
		s.blit(mp, (136, 0))
		self.vram_surf = s

	def get_ram_row(self, row):
		s = ''
		for i in range(0x10):
			b = self.emu.bus.read_at(row * 0x10 + i)
			if i: s += ' '
			s += f'{b:0>2X}'
		return s

	def run(self):
		fn = 'tetris.gb'

		self.emu = emu.Emu()
		self.emu.load_rom(emu.ROM(fn))

		self.last_dis = []
		self.running = False

		while True:
			self.mainloop()
			pygame.display.update()

	def process_events(self):
		for e in pygame.event.get():
			if e.type == pygame.QUIT:
				exit()

			if e.type == pygame.KEYDOWN:
				if e.key == pygame.K_ESCAPE:
					pygame.event.post(pygame.event.Event(pygame.QUIT))
				if e.key == pygame.K_q:
					self.do_one_instruction()
				if e.key == pygame.K_f:
					self.do_instructions_until_frame_then_stop()
				if e.key == pygame.K_w:
					self.running = not self.running
				if e.key == pygame.K_z:
					sss = '00000000000000000000000000000000F000F000FC00FC00FC00FC00F300F3003C003C003C003C003C003C003C003C00F000F000F000F00000000000F300F300000000000000000000000000CF00CF00000000000F000F003F003F000F000F000000000000000000C000C0000F000F00000000000000000000000000F000F000000000000000000000000000F300F300000000000000000000000000C000C000030003000300030003000300FF00FF00C000C000C000C000C000C000C300C300000000000000000000000000FC00FC00F300F300F000F000F000F000F000F0003C003C00FC00FC00FC00FC003C003C00F300F300F300F300F300F300F300F300F300F300C300C300C300C300C300C300CF00CF00CF00CF00CF00CF00CF00CF003C003C003F003F003C003C000F000F003C003C00FC00FC0000000000FC00FC00FC00FC00F000F000F000F000F000F000F300F300F300F300F300F300F000F000C300C300C300C300C300C300FF00FF00CF00CF00CF00CF00CF00CF00C300C3000F000F000F000F000F000F00FC00FC003C004200B900A500B900A50042003C00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
					for i in range(len(sss) // 2):
						cur = sss[i*2:i*2+2]
						x = int(cur, 16)
						self.emu.bus.write_at(0x8000 + i, x)

			if e.type == pygame.MOUSEBUTTONDOWN:
				mx, my = e.pos
				mx -= mx % 8
				my -= my % 8
				print(mx, my)

		return None

	def mainloop(self):
		ev_state = self.process_events()

		if self.running:
			self.do_instructions_until_frame()

		self.win.fill(pygame.Color(248, 248, 248))
		self.win.blit(self.font.render(f'af= {self.emu.cpu.reg_af:0>4X}'), (336, 8))
		self.win.blit(self.font.render(f'bc= {self.emu.cpu.reg_bc:0>4X}'), (336, 16))
		self.win.blit(self.font.render(f'de= {self.emu.cpu.reg_de:0>4X}'), (336, 24))
		self.win.blit(self.font.render(f'hl= {self.emu.cpu.reg_hl:0>4X}'), (336, 32))
		self.win.blit(self.font.render(f'sp= {self.emu.cpu.reg_sp:0>4X}'), (336, 40))
		self.win.blit(self.font.render(f'pc= {self.emu.cpu.reg_pc:0>4X}'), (336, 48))

		self.win.blit(self.font.render(f'lcdc={self.emu.ioreg.data[0x40]:0>2X}'), (408, 8))
		self.win.blit(self.font.render(f'stat={self.emu.ioreg.data[0x41]:0>2X}'), (408, 16))
		self.win.blit(self.font.render(f'ly=  {self.emu.ioreg.data[0x44]:0>2X}'), (408, 24))

		for y,s in enumerate(self.last_dis[::-1]):
			self.win.blit(self.font.render(s), (336, 64 + y * 8))
		# ~ if not self.last_dis is None:
		self.get_vram()
		if not self.vram_surf is None:
			self.win.blit(self.vram_surf, (8, 304))
		for y in range(8):
			s = self.get_ram_row(0x800 + y)
			self.win.blit(self.font.render(s), (408, 304 + y * 8))
		self.win.blit(self.font.render(f'{self.emu.bus.frame_cycles:>5}'), (480, 8))

if __name__ == '__main__':
	import sys
	BREAKPOINT = int(sys.argv[1], 16)
	game = Game()
	game.run()
