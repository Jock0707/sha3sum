PREFIX    = /usr
MANPREFIX = $(PREFIX)/share/man
LIBEXEC   = libexec

CC = c99

COMMON_SANITIZE = -fsanitize=alignment,shift,signed-integer-overflow,object-size,null,undefined,bounds,address
CLANG_SANITIZE  = -O1 $(COMMON_SANITIZE),cfi -flto -fvisibility=hidden -fno-sanitize-trap=cfi
GCC_SANITIZE    = -O1 $(COMMON_SANITIZE)
#SANITIZE        = $(CLANG_SANITIZE)
#SANITIZE        = $(GCC_SANITIZE)

CPPFLAGS =
CFLAGS   = $(SANITIZE)
LDFLAGS  = $(SANITIZE) -lkeccak
