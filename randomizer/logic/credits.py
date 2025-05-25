import random

from randomizer.logic import utils
from randomizer.logic.dialogs import allocate_string
from randomizer.logic.patch import Patch


'''
IMPORTANT NOTES ABOUT MODIFYING:
* The fontset is only UPPER CASE A-Z, space and period. Everything else looks like a space.
* The font/color is dependant on the Y position. Dunno why.
* We're basically out of credits space. Can't add more cards, but could add more titles to those cards.
** Changing this might be hard.
** Dunno if the length is hard coded in the code, or if moving the string table would solve the space problem.
* Watch the whole credits! There's a chance it can freeze at the end or corrupt the firework screen if you do it wrong.

'''

EMPTY_STRING = '                                       '

def to_str(string):
    return ''.join([chr(i + ord('A') - 1) for i in string]).replace('\\', ' ').replace('[', '.')

def inv_str(string):
    string = string.replace(' ', '\\').replace('.', '[').replace('_', ']')
    return chr(len(string)) + ''.join([chr(ord(i) - ord('A') + 1) for i in string])

class Credits(object):
    def __init__(self, table_offset=0):
        self.strings = {}
        self.inv_strings = {}
        self.acc = []
        self.table_offset = table_offset
        self.current_credits = []
        self.current_titles = []

    def add(self, x, y, font, string, scroll=0):
        assert len(string) <= len(EMPTY_STRING)
        if string in self.inv_strings:
            dex = self.inv_strings[string]
        else:
            dex = len(self.strings) + self.table_offset
            self.strings[dex] = string
            self.inv_strings[string] = dex
        self.acc += [0xE3, 0x12, dex, x, y, font, scroll]

    def end_thing(self, delay):
        self.acc += [0xE3, 0x00, 0x0F, 0x02, 0x0B, 0x16, 0x00, 0x01, 0x03, 0x04, 0x10, delay, 0x01]

    def end_thing_2(self, delay):
        self.acc += [0xE3, 0x00, 0x0F, 0x02, 0x16, 0x0B, 0x00, 0x01, 0x03, 0x04, 0x10, delay, 0x00]

    def end_thing_3(self, delay):
        self.acc += [0xE3, 0x00, 0x0F, 0x02, 0x16, 0x0B, 0x00, 0x09, 0x0B, 0x04, 0x10, delay, 0x00]

    def end_thing_4(self, delay):
        self.acc += [0xE3, 0x00, 0x0F, 0x02, 0x0B, 0x16, 0x00, 0x09, 0x0B, 0x04, 0x10, delay, 0x00]

    def clear(self, words):
        for (x, y, font) in words:
            self.add(x, y, font, EMPTY_STRING)
        del words[:]

    # Yeah, got into a OpenGL vibe here.
    def begin_credits(self):
        pass

    def add_credit(self, x, y, font, string, scroll=0):
        self.current_credits.append((x, y, font))
        self.add(x, y, font, string, scroll)

    def end_credits(self, delay_1, delay_2):
        self.end_thing(delay_1)
        self.end_thing_2(delay_2)
        self.clear(self.current_credits)

    def begin_titles(self, delay):
        self.end_thing_3(delay)
        self.clear(self.current_titles)

    def add_title(self, x, y, font, string, scroll=0):
        self.current_titles.append((x, y, font))
        self.add(x, y, font, string, scroll)

    def end_titles(self, delay):
        self.end_thing_4(delay)

    def finalize(self):
        # Return a patch next time...
        acc = []
        credit_start = 0x3FDBB0
        credit_len = 3380
        string_table_start = 0x3FE8E4
        string_table_size = len(self.strings) * 2
        assert len(self.acc) <= credit_len
        # Fill the unused section of credits script with 0.
        # This is very important.
        self.acc += (3380 - len(self.acc)) * [0]

        free_list = {
            0x3f9c40: 952,
            credit_start + len(self.acc): credit_len - len(self.acc),
            string_table_start + string_table_size: 2080 - string_table_size
        }

        patch = Patch()
        patch.add_data(credit_start, bytearray(self.acc))
        for i in range(len(self.strings)):
            string = inv_str(self.strings[i])
            base = allocate_string(len(string), free_list)
            patch.add_data(base, string)
            patch.add_data(string_table_start + i*2, utils.ByteField(base & 0xFFFF, num_bytes=2).as_bytes())

        # Underscore
        patch.add_data(0x3FFDDA, '\x3F\xC0\x7F\x80')
        return patch

END_CREDITS_DELAY_1 = 34
END_CREDITS_DELAY_2 = 40
BEGIN_TITLES_DELAY = 50
END_TITLES_DELAY = 40


# LINE 1, LINE 2, LINE 3. put EMPTY_STRING if you don't have anything.
DEV_MESSAGES = [
    ('DONT TRY IT...ALANIM.', 'I ALREADY DID IT.', 'PAST ALANIM'),
    ('NOW TRY IT', 'BLINDFOLDED', 'PATCDR'),
    ('ILL FIX IT', 'ONE OF THESE DAYS.', 'PIDGE'),
]

# Takes world because everything does.
# If we every implement stats, we'll need it, probably.
def update_credits(world):
    credits = Credits()
    credits.begin_credits()
    credits.add_credit(0x80, 0x80, 0xc0, 'ORIGINAL')
    credits.add_credit(0x80, 0x40, 0x81, 'CREDITS')
    credits.end_credits(END_CREDITS_DELAY_1, END_CREDITS_DELAY_2)

    # Don't need this for the first title.
    # credits.begin_title(BEGIN_TITLES_DELAY)
    credits.add_title(0x80, 0x00, 0x08, '    DIRECTORS       EVENT DESIGN   ')
    credits.end_titles(END_TITLES_DELAY)

    credits.begin_credits()
    credits.add_credit(0x80, 0x80, 0xc0, '    C. FUJIOKA      K. MATSUHARA   ')
    credits.add_credit(0x80, 0x40, 0x81, '    Y. MAEKAWA      Y. MATSUMURA   ')
    credits.add_credit(0x80, 0x00, 0xc2, '                    T. KUDO        ')
    credits.end_credits(END_CREDITS_DELAY_1, END_CREDITS_DELAY_2)

    credits.begin_titles(BEGIN_TITLES_DELAY)
    credits.add_title(0x80, 0x00, 0x08, '    BATTLE DESIGN   MAIN PROGRAM   ')
    credits.end_titles(END_TITLES_DELAY)

    credits.begin_credits()
    credits.add_credit(0x80, 0x80, 0xc0, '    Y. HASEBE       F. FUKAYA      ')
    credits.add_credit(0x80, 0x40, 0x81, '    A. OHTA                        ')
    credits.end_credits(END_CREDITS_DELAY_1, END_CREDITS_DELAY_2)

    credits.begin_titles(BEGIN_TITLES_DELAY)
    credits.add_title(0x80, 0x00, 0x08, '    BATTLE PROGRAM  MENU PROGRAM   ')
    credits.end_titles(END_TITLES_DELAY)

    credits.begin_credits()
    credits.add_credit(0x80, 0x80, 0xc0, '    R. MUTO         M. YOSHIOKA    ')
    credits.add_credit(0x80, 0x40, 0x81, '    AOY                            ')
    credits.end_credits(END_CREDITS_DELAY_1, END_CREDITS_DELAY_2)

    credits.begin_titles(BEGIN_TITLES_DELAY)
    credits.add_title(0x80, 0x00, 0x08, '    GFX COORD.      CHAR. DESIGN   ')
    credits.end_titles(END_TITLES_DELAY)

    credits.begin_credits()
    credits.add_credit(0x80, 0xc0, 0xc0, '    H. MINABA       K. KATO        ')
    credits.add_credit(0x80, 0x80, 0x81, '                    Y. HATAE       ')
    credits.end_credits(END_CREDITS_DELAY_1, END_CREDITS_DELAY_2)

    credits.begin_titles(BEGIN_TITLES_DELAY)
    credits.add_title(0x80, 0x00, 0x08, '  MONSTER DSGN. AND     VFX AND    ')
    credits.add_title(0x80, 0x80, 0x48, '   CHAR. SUPERVS.      PLOT ASST.  ')
    credits.end_titles(END_TITLES_DELAY)

    credits.begin_credits()
    credits.add_credit(0x80, 0x40, 0x81, '   K. KURASHIMA        J. MIFUNE   ')
    credits.end_credits(END_CREDITS_DELAY_1, END_CREDITS_DELAY_2)

    credits.begin_titles(BEGIN_TITLES_DELAY)
    credits.add_title(0x80, 0x00, 0x08, 'MAP DATA COORDINATOR AND ASST.')
    credits.end_titles(END_TITLES_DELAY)

    credits.begin_credits()
    credits.add_credit(0x80, 0xc0, 0xc0, 'K. NISHI')
    credits.add_credit(0x80, 0x80, 0x81, 'T. KURIHARA')
    credits.end_credits(END_CREDITS_DELAY_1, END_CREDITS_DELAY_2)

    credits.begin_titles(BEGIN_TITLES_DELAY)
    credits.add_title(0x80, 0x00, 0x08, 'B.G. MAP DESIGN')
    credits.end_titles(END_TITLES_DELAY)

    credits.begin_credits()
    credits.add_credit(0x80, 0x80, 0xc0, '    A. UEDA         Y. MIYAMOTO    ')
    credits.add_credit(0x80, 0x40, 0x81, '    Y. ABIRU        M. TSUTSUI     ')
    credits.add_credit(0x80, 0x00, 0xc2, '    T. MOGI         Y. SASAKI      ')
    credits.end_credits(END_CREDITS_DELAY_1, END_CREDITS_DELAY_2)

    credits.begin_titles(BEGIN_TITLES_DELAY)
    credits.add_title(0x80, 0x00, 0x08, 'B.G. MAP GRAPHICS')
    credits.end_titles(END_TITLES_DELAY)

    credits.begin_credits()
    credits.add_credit(0x80, 0xc0, 0xc0, 'T. SAKAGUCHI')
    credits.add_credit(0x80, 0x80, 0x81, 'Y. AZUMA')
    credits.end_credits(END_CREDITS_DELAY_1, END_CREDITS_DELAY_2)

    credits.begin_titles(BEGIN_TITLES_DELAY)
    credits.add_title(0x80, 0x00, 0x08, '    MUSIC           SOUND ENGINEER ')
    credits.add_title(0x80, 0x40, 0x49, 'SOUND PROGRAMMER')
    credits.end_titles(END_TITLES_DELAY)

    credits.begin_credits()
    credits.add_credit(0x80, 0x80, 0xc0, '    Y. SHIMOMURA     T. SUGAWARA   ')
    credits.add_credit(0x80, 0xc0, 0x81, '    H. SUZUKI  AND  M. WATANABE    ')
    credits.end_credits(END_CREDITS_DELAY_1, END_CREDITS_DELAY_2)

    credits.begin_titles(BEGIN_TITLES_DELAY)
    credits.add_title(0x80, 0x00, 0x08, '    SOUND FX        PUBLICITY      ')
    credits.end_titles(END_TITLES_DELAY)

    credits.begin_credits()
    credits.add_credit(0x80, 0x80, 0xc0, '    C. MINEKAWA     Y. HIRATA      ')
    credits.add_credit(0x80, 0x40, 0x81, '    Y. HIROTA       K. MAEDA       ')
    credits.add_credit(0x80, 0x00, 0xc2, '    K. TAKAHASHI                   ')
    credits.end_credits(END_CREDITS_DELAY_1, END_CREDITS_DELAY_2)

    credits.begin_titles(BEGIN_TITLES_DELAY)
    credits.add_title(0x80, 0x00, 0x08, 'TRANSLATION')
    credits.add_title(0x80, 0x40, 0x49, '    COORDINATOR     SUPERVISOR     ')
    credits.end_titles(END_TITLES_DELAY)

    credits.begin_credits()
    credits.add_credit(0x80, 0x80, 0xc0, '    R. MARUYA       N. WADA        ')
    credits.add_credit(0x80, 0xc0, 0x81, '    A. ITO          T. WOOLSEY     ')
    credits.end_credits(END_CREDITS_DELAY_1, END_CREDITS_DELAY_2)

    credits.begin_titles(BEGIN_TITLES_DELAY)
    credits.add_title(0x80, 0x00, 0x08, 'MONITOR COORDINATORS')
    credits.end_titles(END_TITLES_DELAY)

    credits.begin_credits()
    credits.add_credit(0x80, 0x80, 0xc0, 'H. HAMADA Y. CHIBA  K.KAWASAKI')
    credits.add_credit(0x80, 0x40, 0x81, 'N. HANADA R. KOUDA  R.KOMATSU ')
    credits.add_credit(0x80, 0x00, 0xc2, 'K. KANEKO H. MASUDA Y.SHIBANO ')
    credits.end_credits(END_CREDITS_DELAY_1, END_CREDITS_DELAY_2)

    credits.begin_titles(BEGIN_TITLES_DELAY)
    credits.add_title(0x80, 0x00, 0x08, 'SPECIAL THANKS TO')
    credits.end_titles(END_TITLES_DELAY)

    credits.begin_credits()
    credits.add_credit(0x80, 0x80, 0xc0, '    S. HASHIMOTO    K. HASHIMOTO   ')
    credits.add_credit(0x80, 0x40, 0x81, '    H. OHMORI       M. SAKAKIBARA  ')
    credits.add_credit(0x80, 0x00, 0xc2, '    T. KAYANO       A. YAMAGUCHI   ')
    credits.end_credits(END_CREDITS_DELAY_1, END_CREDITS_DELAY_2)

    credits.begin_titles(BEGIN_TITLES_DELAY)
    credits.add_title(0x80, 0x00, 0x08, 'EXTRA SPECIAL THANKS TO')
    credits.end_titles(END_TITLES_DELAY)

    credits.begin_credits()
    credits.add_credit(0x80, 0x80, 0xc0, 'H. ITOU')
    credits.add_credit(0x80, 0x40, 0x81, 'N. UEMATSU')
    credits.add_credit(0x80, 0x00, 0xc2, 'T. NOMURA')
    credits.end_credits(END_CREDITS_DELAY_1, END_CREDITS_DELAY_2)

    credits.begin_titles(BEGIN_TITLES_DELAY)
    credits.add_title(0x80, 0x00, 0x08, 'PRODUCTION SUPERVISOR')
    credits.end_titles(END_TITLES_DELAY)

    credits.begin_credits()
    credits.add_credit(0x80, 0x80, 0xc0, 'H. SAKAGUCHI')
    credits.end_credits(END_CREDITS_DELAY_1, END_CREDITS_DELAY_2)

    credits.begin_titles(BEGIN_TITLES_DELAY)
    credits.add_title(0x80, 0x00, 0x08, 'CHAR. AND SCREENPLAY ADVISORS')
    credits.end_titles(END_TITLES_DELAY)

    credits.begin_credits()
    credits.add_credit(0x80, 0xc0, 0xc0, '    Y. KOTABE       K. TANABE      ')
    credits.add_credit(0x80, 0x80, 0x81, '                    A. TEJIMA      ')
    credits.end_credits(END_CREDITS_DELAY_1, END_CREDITS_DELAY_2)

    credits.begin_titles(BEGIN_TITLES_DELAY)
    credits.add_title(0x80, 0x00, 0x08, 'C.G. MODEL DESIGNER')
    credits.end_titles(END_TITLES_DELAY)

    credits.begin_credits()
    credits.add_credit(0x80, 0xc0, 0xc0, 'S. TAKAHASHI')
    credits.end_credits(END_CREDITS_DELAY_1, END_CREDITS_DELAY_2)

    credits.begin_titles(BEGIN_TITLES_DELAY)
    credits.add_title(0x80, 0x00, 0x08, 'SPECIAL THANKS TO')
    credits.end_titles(END_TITLES_DELAY)

    credits.begin_credits()
    credits.add_credit(0x80, 0x80, 0xc0, 'T. KURIBAYASHI')
    credits.add_credit(0x80, 0x40, 0x81, 'H. YAMADA     ')
    credits.add_credit(0x80, 0x00, 0xc2, 'K. KONDO      ')
    credits.end_credits(END_CREDITS_DELAY_1, END_CREDITS_DELAY_2)

    credits.begin_titles(BEGIN_TITLES_DELAY)
    credits.add_title(0x80, 0x00, 0x08, 'NOA PRODUCTION ANALYSIS')
    credits.end_titles(END_TITLES_DELAY)

    credits.begin_credits()
    credits.add_credit(0x80, 0xc0, 0xc0, 'J. WORNELL')
    credits.add_credit(0x80, 0x80, 0x81, 'K. MCDONALD')
    credits.end_credits(END_CREDITS_DELAY_1, END_CREDITS_DELAY_2)

    credits.begin_titles(BEGIN_TITLES_DELAY)
    credits.add_title(0x80, 0x00, 0x08, 'PRODUCER')
    credits.end_titles(END_TITLES_DELAY)

    credits.begin_credits()
    credits.add_credit(0x80, 0xc0, 0xc0, 'S. MIYAMOTO')
    credits.end_credits(END_CREDITS_DELAY_1, END_CREDITS_DELAY_2)

    credits.begin_titles(BEGIN_TITLES_DELAY)
    credits.add_title(0x80, 0x00, 0x08, 'EXECUTIVE PRODUCER')
    credits.end_titles(END_TITLES_DELAY)

    credits.begin_credits()
    credits.add_credit(0x80, 0xc0, 0xc0, 'H. YAMAUCHI AND T. MIZUNO')
    credits.end_credits(END_CREDITS_DELAY_1, END_CREDITS_DELAY_2)

    credits.begin_titles(BEGIN_TITLES_DELAY)
    credits.end_titles(END_TITLES_DELAY)

    credits.begin_credits()
    credits.add_credit(0x80, 0xc0, 0xc0, 'RANDOMIZER')
    credits.add_credit(0x80, 0x80, 0x81, 'CREDITS')
    credits.end_credits(END_CREDITS_DELAY_1, END_CREDITS_DELAY_2)

    credits.begin_titles(BEGIN_TITLES_DELAY)
    credits.add_title(0x80, 0x00, 0x08, 'CUTEST SHIP')
    credits.end_titles(END_TITLES_DELAY)

    credits.begin_credits()
    credits.add_credit(0x80, 0x80, 0xc0, 'VERNIY')
    credits.end_credits(END_CREDITS_DELAY_1, END_CREDITS_DELAY_2)

    credits.begin_titles(BEGIN_TITLES_DELAY)
    credits.add_title(0x80, 0x00, 0x08, 'SPECIAL THANKS')
    credits.end_titles(END_TITLES_DELAY)

    credits.end_thing(END_CREDITS_DELAY_1)

    return credits.finalize()
