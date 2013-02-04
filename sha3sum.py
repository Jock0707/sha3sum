#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
sha3sum – SHA-3 (Keccak) checksum calculator

Copyright © 2013  Mattias Andrée (maandree@member.fsf.org)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import sys
import os


class SHA3:
    '''
    SHA-3/Keccak hash algorithm implementation
    
    @author  Mattias Andrée (maandree@member.fsf.org)
    '''
    
    
    RC=[0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000,
        0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
        0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
        0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003,
        0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
        0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008]
    '''
    :list<int>  Round contants
    '''
    
    B = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    '''
    :list<list<int>>  Keccak-f round temporary
    '''
    
    C = [0, 0, 0, 0, 0]
    '''
    :list<int>  Keccak-f round temporary
    '''
    

    (r, c, n, b, w, wmod, l, nr) = (0, 0, 0, 0, 0, 0, 0, 0)
    '''
       r:int  The bitrate
       c:int  The capacity
       n:int  The output size
       b:int  The state size
       w:int  The word size
    wmod:int  The word mask
       l:int  ℓ, the binary logarithm of the word size
      nr:int  12 + 2ℓ, the number of rounds
    '''
    
    S = None
    '''
    :list<list<int>>  The current state
    '''
    
    M = None
    '''
    :bytes  Left over water to fill the sponge with at next update
    '''
    
    
    
    @staticmethod
    def rotate(x, n):
        '''
        Rotate a word
        
        @param   x:int  The value to rotate
        @param   n:int  Rotation steps
        @return   :int  The value rotated
        '''
        return ((x >> (SHA3.w - (n % SHA3.w))) + (x << (n % SHA3.w))) & SHA3.wmod
    
    
    @staticmethod
    def lb(x):
        '''
        Binary logarithm
        
        @param   x:int  The value of which to calculate the binary logarithm
        @return   :int  The binary logarithm
        '''
        rc_a = 0 if (x & 0xFF00) == 0 else 8
        rc_b = 0 if (x & 0xF0F0) == 0 else 4
        rc_c = 0 if (x & 0xCCCC) == 0 else 2
        rc_d = 0 if (x & 0xAAAA) == 0 else 1
        return (rc_a + rc_b) + (rc_c + rc_d)
    
    
    @staticmethod
    def keccakFRound(A, rc):
        '''
        Perform one round of computation
        
        @param   A:list<int>  The current state
        @param  rc:int        Round constant
        '''
        # θ step (step 1 and 2 of 3)
        SHA3.C[0] = (A[0]  ^ A[1])  ^ (A[2]  ^ A[3])  ^ A[4]
        SHA3.C[1] = (A[5]  ^ A[6])  ^ (A[7]  ^ A[8])  ^ A[9]
        SHA3.C[2] = (A[10] ^ A[11]) ^ (A[12] ^ A[13]) ^ A[14]
        SHA3.C[3] = (A[15] ^ A[16]) ^ (A[17] ^ A[18]) ^ A[19]
        SHA3.C[4] = (A[20] ^ A[21]) ^ (A[22] ^ A[23]) ^ A[24]
        
        da = SHA3.C[4] ^ SHA3.rotate(SHA3.C[1], 1)
        db = SHA3.C[0] ^ SHA3.rotate(SHA3.C[2], 1)
        dc = SHA3.C[1] ^ SHA3.rotate(SHA3.C[3], 1)
        dd = SHA3.C[2] ^ SHA3.rotate(SHA3.C[4], 1)
        de = SHA3.C[3] ^ SHA3.rotate(SHA3.C[0], 1)
        
        # ρ and π steps, with last part of θ
        SHA3.B[0] = SHA3.rotate(A[0] ^ da, 0)
        SHA3.B[1] = SHA3.rotate(A[15] ^ dd, 28)
        SHA3.B[2] = SHA3.rotate(A[5] ^ db, 1)
        SHA3.B[3] = SHA3.rotate(A[20] ^ de, 27)
        SHA3.B[4] = SHA3.rotate(A[10] ^ dc, 62)
        
        SHA3.B[5] = SHA3.rotate(A[6] ^ db, 44)
        SHA3.B[6] = SHA3.rotate(A[21] ^ de, 20)
        SHA3.B[7] = SHA3.rotate(A[11] ^ dc, 6)
        SHA3.B[8] = SHA3.rotate(A[1] ^ da, 36)
        SHA3.B[9] = SHA3.rotate(A[16] ^ dd, 55)
        
        SHA3.B[10] = SHA3.rotate(A[12] ^ dc, 43)
        SHA3.B[11] = SHA3.rotate(A[2] ^ da, 3)
        SHA3.B[12] = SHA3.rotate(A[17] ^ dd, 25)
        SHA3.B[13] = SHA3.rotate(A[7] ^ db, 10)
        SHA3.B[14] = SHA3.rotate(A[22] ^ de, 39)
        
        SHA3.B[15] = SHA3.rotate(A[18] ^ dd, 21)
        SHA3.B[16] = SHA3.rotate(A[8] ^ db, 45)
        SHA3.B[17] = SHA3.rotate(A[23] ^ de, 8)
        SHA3.B[18] = SHA3.rotate(A[13] ^ dc, 15)
        SHA3.B[19] = SHA3.rotate(A[3] ^ da, 41)
        
        SHA3.B[20] = SHA3.rotate(A[24] ^ de, 14)
        SHA3.B[21] = SHA3.rotate(A[14] ^ dc, 61)
        SHA3.B[22] = SHA3.rotate(A[4] ^ da, 18)
        SHA3.B[23] = SHA3.rotate(A[19] ^ dd, 56)
        SHA3.B[24] = SHA3.rotate(A[9] ^ db, 2)
        
        # ξ step
        A[0] = SHA3.B[0] ^ ((~(SHA3.B[5])) & SHA3.B[10])
        A[1] = SHA3.B[1] ^ ((~(SHA3.B[6])) & SHA3.B[11])
        A[2] = SHA3.B[2] ^ ((~(SHA3.B[7])) & SHA3.B[12])
        A[3] = SHA3.B[3] ^ ((~(SHA3.B[8])) & SHA3.B[13])
        A[4] = SHA3.B[4] ^ ((~(SHA3.B[9])) & SHA3.B[14])
        
        A[5] = SHA3.B[5] ^ ((~(SHA3.B[10])) & SHA3.B[15])
        A[6] = SHA3.B[6] ^ ((~(SHA3.B[11])) & SHA3.B[16])
        A[7] = SHA3.B[7] ^ ((~(SHA3.B[12])) & SHA3.B[17])
        A[8] = SHA3.B[8] ^ ((~(SHA3.B[13])) & SHA3.B[18])
        A[9] = SHA3.B[9] ^ ((~(SHA3.B[14])) & SHA3.B[19])
        
        A[10] = SHA3.B[10] ^ ((~(SHA3.B[15])) & SHA3.B[20])
        A[11] = SHA3.B[11] ^ ((~(SHA3.B[16])) & SHA3.B[21])
        A[12] = SHA3.B[12] ^ ((~(SHA3.B[17])) & SHA3.B[22])
        A[13] = SHA3.B[13] ^ ((~(SHA3.B[18])) & SHA3.B[23])
        A[14] = SHA3.B[14] ^ ((~(SHA3.B[19])) & SHA3.B[24])
        
        A[15] = SHA3.B[15] ^ ((~(SHA3.B[20])) & SHA3.B[0])
        A[16] = SHA3.B[16] ^ ((~(SHA3.B[21])) & SHA3.B[1])
        A[17] = SHA3.B[17] ^ ((~(SHA3.B[22])) & SHA3.B[2])
        A[18] = SHA3.B[18] ^ ((~(SHA3.B[23])) & SHA3.B[3])
        A[19] = SHA3.B[19] ^ ((~(SHA3.B[24])) & SHA3.B[4])
        
        A[20] = SHA3.B[20] ^ ((~(SHA3.B[0])) & SHA3.B[5])
        A[21] = SHA3.B[21] ^ ((~(SHA3.B[1])) & SHA3.B[6])
        A[22] = SHA3.B[22] ^ ((~(SHA3.B[2])) & SHA3.B[7])
        A[23] = SHA3.B[23] ^ ((~(SHA3.B[3])) & SHA3.B[8])
        A[24] = SHA3.B[24] ^ ((~(SHA3.B[4])) & SHA3.B[9])
        
        # ι step
        A[0] ^= rc
    
    
    @staticmethod
    def keccakF(A):
        '''
        Perform Keccak-f function
        
        @param  A:list<int>  The current state
        '''
        if (SHA3.nr == 24):
            SHA3.keccakFRound(A, 0x0000000000000001)
            SHA3.keccakFRound(A, 0x0000000000008082)
            SHA3.keccakFRound(A, 0x800000000000808A)
            SHA3.keccakFRound(A, 0x8000000080008000)
            SHA3.keccakFRound(A, 0x000000000000808B)
            SHA3.keccakFRound(A, 0x0000000080000001)
            SHA3.keccakFRound(A, 0x8000000080008081)
            SHA3.keccakFRound(A, 0x8000000000008009)
            SHA3.keccakFRound(A, 0x000000000000008A)
            SHA3.keccakFRound(A, 0x0000000000000088)
            SHA3.keccakFRound(A, 0x0000000080008009)
            SHA3.keccakFRound(A, 0x000000008000000A)
            SHA3.keccakFRound(A, 0x000000008000808B)
            SHA3.keccakFRound(A, 0x800000000000008B)
            SHA3.keccakFRound(A, 0x8000000000008089)
            SHA3.keccakFRound(A, 0x8000000000008003)
            SHA3.keccakFRound(A, 0x8000000000008002)
            SHA3.keccakFRound(A, 0x8000000000000080)
            SHA3.keccakFRound(A, 0x000000000000800A)
            SHA3.keccakFRound(A, 0x800000008000000A)
            SHA3.keccakFRound(A, 0x8000000080008081)
            SHA3.keccakFRound(A, 0x8000000000008080)
            SHA3.keccakFRound(A, 0x0000000080000001)
            SHA3.keccakFRound(A, 0x8000000080008008)
        else:
            for i in range(SHA3.nr):
                SHA3.keccakFRound(A, SHA3.RC[i] & SHA3.wmod)
    
    
    @staticmethod
    def toLane(message, rr, ww, off):
        '''
        Convert a chunk of char:s to a word
        
        @param   message:bytes  The message
        @param        rr:int    Bitrate in bytes
        @param        ww:int    Word size in bytes
        @param       off:int    The offset in the message
        @return         :int    Lane
        '''
        rc = 0
        i = off + ww - 1
        n = len(message)
        while i >= off:
            rc <<= 8
            rc |= message[i] if (i < rr) and (i < n) else 0
            i -= 1
        return rc
    
    
    @staticmethod
    def pad10star1(msg, r):
        '''
        pad 10*1
        
        @param   msg:bytes  The message to pad
        @param     n:int    The The message to pad
        @param     r:int    The bitrate
        @return     :str    The message padded
        '''
        nnn = len(msg)
        
        nrf = nnn >> 3
        nbrf = nnn & 7
        ll = nnn % r
        
        bbbb = 1 if nbrf == 0 else ((msg[nrf] >> (8 - nbrf)) | (1 << nbrf))
        
        message = None
        if ((r - 8 <= ll) and (ll <= r - 2)):
            nnn = nrf + 1
            message = [bbbb ^ 128]
        else:
            nnn = (nrf + 1) << 3
            nnn = ((nnn - (nnn % r) + (r - 8)) >> 3) + 1
            message = [0] * (nnn - nrf)
            message[0] = bbbb
            nnn -= nrf
            for i in range(1, nnn):
                message[i] = 0
            message[nnn - 1] = 0x80
        
        return msg[:nrf] + bytes(message)
    
    
    @staticmethod
    def initalise(r, c, n):
        '''
        Initalise Keccak sponge
        
        @param  r:int  The bitrate
        @param  c:int  The capacity
        @param  n:int  The output size
        '''
        SHA3.r = r
        SHA3.c = c
        SHA3.n = n
        SHA3.b = (r + c)
        SHA3.w = SHA3.b // 25
        SHA3.l = SHA3.lb(SHA3.w)
        SHA3.nr = 12 + (SHA3.l << 1)
        SHA3.wmod = (1 << SHA3.w) - 1
        SHA3.S=[0, 0, 0, 0, 0,
                0, 0, 0, 0, 0,
                0, 0, 0, 0, 0,
                0, 0, 0, 0, 0,
                0, 0, 0, 0, 0]
        SHA3.M = bytes([])
    
    
    @staticmethod
    def update(msg):
        '''
        Absorb the more of the message message to the Keccak sponge
        
        @param  msg:bytes  The partial message
        '''
        rr = SHA3.r >> 3
        ww = SHA3.w >> 3
        
        SHA3.M += msg
        SHA3.pad10star1(SHA3.M, SHA3.r)
        nnn = len(SHA3.M)
        nnn -= nnn % ((SHA3.r * SHA3.b) >> 3)
        message = SHA3.M[:nnn]
        SHA3.M = SHA3.M[nnn:]
        
        # Absorbing phase
        msg_i =[0, 0, 0, 0, 0,
                0, 0, 0, 0, 0,
                0, 0, 0, 0, 0,
                0, 0, 0, 0, 0,
                0, 0, 0, 0, 0]
        m = nnn
        for i in range(0, m, rr):
            for j in range(25):
                SHA3.S[j] ^= SHA3.toLane(message[i:], rr, ww, j * ww)
            SHA3.keccakF(SHA3.S)
    
    
    @staticmethod
    def digest(msg = None):
        '''
        Absorb the last part of the message and squeeze the Keccak sponge
        
        @param  msg:bytes  The rest of the message
        '''
        if msg is None:
            msg = bytes([])
        message = SHA3.pad10star1(SHA3.M + msg, SHA3.r)
        SHA3.M = None
        nnn = len(message)
        rc = [0] * ((SHA3.n + 7) >> 3)
        ptr = 0
        
        rr = SHA3.r >> 3
        nn = SHA3.n >> 3
        ww = SHA3.w >> 3
        
        # Absorbing phase
        msg_i =[0, 0, 0, 0, 0,
                0, 0, 0, 0, 0,
                0, 0, 0, 0, 0,
                0, 0, 0, 0, 0,
                0, 0, 0, 0, 0]
        m = nnn
        for i in range(0, m, rr):
            for j in range(25):
                SHA3.S[j] ^= SHA3.toLane(message[i:], rr, ww, j * ww)
            SHA3.keccakF(SHA3.S)
        
        # Squeezing phase
        olen = SHA3.n
        j = 0
        ni = min(25, rr)
        while (olen > 0):
            i = 0
            while i < ni and (j < nn):
                v = SHA3.S[i]
                for _ in range(ww):
                    if (j < nn):
                        rc[ptr] = v & 255
                        ptr += 1
                    v >>= 8
                    j += 1
                i += 1
            olen -= SHA3.r
            if olen > 0:
                SHA3.keccakF(S)
        
        return bytes(rc)


if __name__ == '__main__':
    cmd = sys.argv[0]
    args = sys.argv[1:]
    if '/' in cmd:
        cmd = cmd[cmd.rfind('/') + 1:]
    if cmd.endswith('.py'):
        cmd = cmd[:-3]
    
    o = 512           # --outputsize
    if   cmd == 'sha3-224sum':  o = 224
    elif cmd == 'sha3-256sum':  o = 256
    elif cmd == 'sha3-384sum':  o = 384
    elif cmd == 'sha3-512sum':  o = 512
    s = 1600          # --statesize
    r = s - (o << 1)  # --bitrate
    c = s - r         # --capacity
    w = s // 25       # --wordsize
    i = 1             # --iterations
    binary = False
    
    (_r, _c, _w, _o, _s, _i) = (r, c, w, o, s, i)
    
    files = []
    dashed = False
    linger = None
    
    for arg in args + [None]:
        if linger is not None:
            if linger[0] in ('-h', '--help'):
                sys.stderr.buffer.write(('''
SHA-3/Keccak checksum calculator

USAGE:	sha3sum [option...] < file
	sha3sum [option...] file...


OPTIONS:
	-r BITRATE
	--bitrate	The bitrate to use for SHA-3.		(default: %d)
	
	-c CAPACITY
	--capacity	The capacity to use for SHA-3.		(default: %d)
	
	-w WORDSIZE
	--wordsize	The word size to use for SHA-3.		(default: %d)
	
	-o OUTPUTSIZE
	--outputsize	The output size to use for SHA-3.	(default: %d)
	
	-s STATESIZE
	--statesize	The state size to use for SHA-3.	(default: %d)
	
	-i ITERATIONS
	--iterations	The number of hash iterations to run.	(default: %d)

	-b
	--binary	Print the checksum in binary, rather than hexadecimal.


COPYRIGHT:

Copyright © 2013  Mattias Andrée (maandree@member.fsf.org)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

''' % (_r, _c, _w, _o, _s, _i)).encode('utf-8'))
                sys.stderr.buffer.flush()
                exit(2)
            else:
                if linger[1] is None:
                    linger[1] = arg
                    arg = None
                if linger[0] in ('-r', '--bitrate'):
                    r = int(linger[1])
                    o = (s - r) >> 1
                elif linger[0] in ('-c', '--capacity'):
                    c = int(linger[1])
                    r = s - c
                elif linger[0] in ('-w', '--wordsize'):
                    w = int(linger[1])
                    s = w * 25
                elif linger[0] in ('-o', '--outputsize'):
                    o = int(linger[1])
                    r = s - (o << 1)
                elif linger[0] in ('-s', '--statesize'):
                    s = int(linger[1])
                    r = s - (o << 1)
                elif linger[0] in ('-i', '--iterations'):
                    i = int(linger[1])
                else:
                    sys.stderr.buffer.write((sys.argv[0] + ': unrecognised option: ' + linger[0] + '\n').encode('utf-8'))
                    sys.stdout.buffer.flush()
                    exit(1)
            linger = None
            if arg is None:
                continue
        if arg is None:
            continue
        if dashed:
            files.append(None if arg == '-' else arg)
        elif arg == '--':
            dashed = True
        elif arg == '-':
            files.append(None)
        elif arg.startswith('--'):
            if '=' in arg:
                linger = (arg[:arg.find('=')], arg[arg.find('=') + 1:])
            else:
                if arg == '--binary':
                    binary = True
                else:
                    linger = [arg, None]
        elif arg.startswith('-'):
            arg = arg[1:]
            if arg[0] == 'b':
                binary = True
                arg = arg[1:]
            elif len(arg) == 1:
                linger = ['-' + arg, None]
            else:
                linger = ['-' + arg[0], arg[1:]]
        else:
            files.append(arg)
    
    if len(files) == 0:
        files.append(None)
    if i < 1:
        sys.stdout.buffer.write((sys.argv[0] + ': sorry, I will only do at least one iteration!\n').encode('utf-8'))
        sys.stdout.buffer.flush()
        exit(3)
    stdin = None
    for filename in files:
        if (filename is None) and (stdin is not None):
            print(stdin)
            continue
        rc = ''
        fn = '/dev/stdin' if filename is None else filename
        with open(fn, 'rb') as file:
            SHA3.initalise(r, c, o)
            blksize = os.stat(os.path.realpath(fn)).st_size
            SHA3.update(file.read(blksize))
            bs = SHA3.digest(file.read())
            for _ in range(1, i):
                SHA3.initalise(r, c, o)
                bs = SHA3.digest(bs)
            if binary:
                if filename is None:
                    stdin = bs
                sys.stdout.buffer.write(bs)
                sys.stdout.buffer.flush()
            else:
                for b in bs:
                    rc += "0123456789ABCDEF"[b >> 4]
                    rc += "0123456789ABCDEF"[b & 15]
                rc += ' ' + ('-' if filename is None else filename) + '\n'
                if filename is None:
                    stdin = rc
                sys.stdout.buffer.write(rc.encode('UTF-8'))
                sys.stdout.buffer.flush()

