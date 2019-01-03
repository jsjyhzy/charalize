'''char.py

Define the fullwidth characters
'''

SPACE = chr(12288)

# Ref
# http://www.unicode.org/charts/PDF/UFF00.pdf
EN = ''.join([chr(i) for i in range(65281, 65375)])

# Ref
# http://www.unicode.org/charts/PDF/U3040.pdf
# http://www.unicode.org/charts/PDF/U30A0.pdf
JP = ''.join([chr(i) for i in range(12353, 12439)] +
             [chr(i) for i in range(12449, 12539)])

BOX = ''.join([chr(i) for i in range(9472, 9600)])

ALL = SPACE + EN + JP + BOX
