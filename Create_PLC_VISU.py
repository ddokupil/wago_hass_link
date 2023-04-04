#!/usr/bin/python3
import argparse

# define command-line arguments
parser = argparse.ArgumentParser(description='Generate visualization file for import in codesys')
parser.add_argument('-i', '--input', required=True, help='path to input file')
parser.add_argument('-o', '--output', default='PLC_VISU.EXP', help='path to output file')
args = parser.parse_args()

# read variables from input file
with open(args.input) as f:
    variables = [line.strip() for line in f.readlines()]

# define template, header, and footer
header = """(* @PATH := '' *)

VISUALISATION PLC_VISU _VISU_TYPES : 1,3
_BG_BMP : ''
_TEXT : 117
_PAINTZOOM : 100"""

template = """_SIMPLE : 1
_LINEWIDTH : 0
_NOCOLORS : 0,1
_POS : 280,280,301,291,290,280
_COLORS : 32768,0,65280,0,0
_VARIABLES : '','','','','','','',''
_THRESH : '','{}','',''
_DSP : '','',''
_ZOOM : ''
_INPUT : 0
_TEXT : 5,4294967284,400,0,39,0,0,0
_FONT : ''
_EXEC : ''
_TEXTVARIABLES : '','','','',''
_COLORVARIABLES : '','','','','',''
_ACCESSLEVELS : 2,2,2,2,2,2,2,2
_OBJECT : 0,0
_THRESH2 : '','','',''
_INPUTTYPE : '','',''
_HIDDENINPUT : 0
_END_ELEM
(* @TEXTSCALINGVARS := '_TEXTSCALINGVARS: $'$',$'$'' *)
(* @EXTENDEDSIMPLESHAPE := '_SIMPLE: 0' *)
(* @INPUTTAPFALSE := '_INPUTTAPFALSE: 0' *)"""

footer = "\nEND_VISUALISATION"

# create output file
with open(args.output, 'w') as f:
    # write header
    f.write(header)
    f.write('\n\n')

    # iterate over variables and write a new template for each one
    for i, variable in enumerate(variables):
        new_string = template.format(variable)
        f.write(new_string)
        if i != len(variables) - 1:  # check if this is not the last iteration
            f.write('\n\n')

    # write footer
    f.write(footer)
    f.write('\n')
