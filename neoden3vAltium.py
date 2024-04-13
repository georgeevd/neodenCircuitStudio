# It is important to note that this script will include your PTH components as well as your SMT components.
# You will need to later select which parts are skipped or not.
# Copyright 2018 Michael Moskie
# mod 2020 to Python3
import sys
from decimal import Decimal
import argparse
import re


class Columns:
    def __init__(self):
        self.designator_position = 0
        self.comment_position = 1
        self.layer_position = 2
        self.footprint_position = 3
        self.x_position = 4
        self.y_position = 5
        self.rotation_position = 6
    def print(self):
        print("Des %i Com %i L %i fp %i X %i Y %i Rot %i" %
              (self.designator_position, self.comment_position, self.layer_position,
               self.footprint_position, self.x_position, self.y_position, self.rotation_position))


class Component:
    # just a structure to represent a physical component
    def __init__(self, line, columns):
        # "Designator","Comment","Layer","Footprint","Center-X(mm)","Center-Y(mm)","Rotation","Description"
        self.Designator = line.split(',')[columns.designator_position]
        self.Footprint = (str(line.split(',')[columns.footprint_position]).replace("\"", ""))
        self.Layer = (str(line.split(',')[columns.layer_position]).replace("\"", ""))
        self.X = line.split(',')[columns.x_position].replace("\"", "")
        self.Y = line.split(',')[columns.y_position].replace("\"", "")
        #self.Layer = line.split(',')[2].replace("\"", "")
        if self.Layer == "top":
            self.Layer = "TopLayer"
        else:
            if self.Layer == "bottom" or self.Layer == "bot":
                self.Layer = "BottomLayer"
        self.Rotation = line.split(',')[columns.rotation_position].replace("\"", "")
        self.RawRotation = self.Rotation
        self.Comment = line.split(',')[columns.comment_position].replace("\"", "")
        self.nozzle = 0
        self.feeder = 0
        self.skip = 'No'
        self.Correction = "0"



class CorrectionForElement:
    def __init__(self, footprint, correction):
        self.Footprint = footprint
        self.Correction = correction


class Part:
    def __init__(self, footprint, comment, part='', feeder=0, nozzle=0):
        self.Footprint = footprint
        self.Comment = comment
        self.feeder = feeder
        self.nozzle = nozzle
        self.part = part
        self.quantity = 1


class NeoDenConverter:
    def make_component_list(self):
        counter = 0
        preamble = True

        designator_regexp = "(Designator)|(Ref)"
        comment_regexp = "(Comment)|((^ *Val,)|(, *Val))"
        layer_regexp = "([,\"']{0,}[^a-zA-Z]Layer)|(Side)"
        footprint_regexp = "(Footprint)|(Package)"
        x_regexp = "(Center-X)|(PosX)"
        y_regexp = "(Center-Y)|(PosY)"
        rotation_regexp = "(Rotation)|(Rot)"

        for line in self.AltiumOutputFile:
            """if counter < 13:
                # throw away the header.
                pass"""
            if preamble:
                x_position = re.search(x_regexp, line, re.MULTILINE)
                y_position = re.search(y_regexp, line, re.MULTILINE)
                rotation = re.search(rotation_regexp, line, re.MULTILINE)
                if x_position is not None and y_position is not None and rotation is not None:
                    designator = re.search(designator_regexp, line, re.MULTILINE)
                    comment = re.search(comment_regexp, line, re.MULTILINE)
                    layer = re.search(layer_regexp, line, re.MULTILINE)
                    footprint = re.search(footprint_regexp, line, re.MULTILINE)

                    self.columns.x_position = line[0:x_position.span()[0] + 1].count(",")
                    self.columns.y_position = line[0:y_position.span()[0] + 1].count(",")
                    self.columns.rotation_position = line[0:rotation.span()[0] + 1].count(",")
                    self.columns.designator_position = line[0:designator.span()[0] + 1].count(",")
                    self.columns.comment_position = line[0:comment.span()[0] + 1].count(",")
                    self.columns.layer_position = line[0:layer.span()[1]].count(",")
                    print(line[0:layer.span()[0] + 2])
                    self.columns.footprint_position = line[0:footprint.span()[0] + 1].count(",")
                    print("COLUMNS:")
                    self.columns.print()
                    preamble = False
            else:
                new_element = Component(line, self.columns)
                self.components.append(new_element)
                self.footprints.add(new_element.Footprint)

            counter += 1

    def get_distances_from_first_chip(self):
        first_chip_x = 0
        first_chip_y = 0
        counter = 0
        for comp in self.components:
            if counter == 0:
                # this is the first component
                first_chip_x = comp.X
                first_chip_y = comp.Y
                comp.X = 0
                comp.Y = 0
            else:
                comp.X = float(comp.X) - float(first_chip_x)
                comp.Y = float(comp.Y) - float(first_chip_y)
            counter += 1

    def apply_machine_positions_2_components(self):
        for comp in self.components:
            comp.X += self.firstChipPhysicalX
            comp.Y += self.firstChipPhysicalY

    def __feeder_n_nozzle_str__(self, component):
        if self.feeders_data_flag:
            str_preamble = "comp," + str(component.feeder) + ", " + str(component.nozzle) + ", "
        else:
            part = component.Footprint + "/" + component.Comment
            str_preamble = "comp," + "FEEDER_4_" + part + ",NOZZLE_4_" + part + "," + ", "
        return str_preamble

    def create_output_file(self, layer):
        output_file = open(self.AltiumOutputFile.name.replace(".csv", "-NEODEN.csv"), "w")

        output_file.write("# Mirror,First component X,First component Y,Rotation,Skip,\n" +
                        "mirror, " + str(self.components[0].X) + ", " + str(self.components[0].Y) + ", " +
                        str(self.components[0].Rotation) + ", No,\n\n")
        output_file.write("#Chip,Feeder ID,Nozzle,Name,Value,Footprint,X,Y,Rotation,Skip\n")
        for comp in self.components:
            if not layer or comp.Layer == layer:
                out_line = self.__feeder_n_nozzle_str__(comp) +\
                           str(comp.Designator).replace("\"", "") + "," + \
                           comp.Comment + "," + str(comp.Footprint).replace("\"", "") + "," + \
                           str(round(Decimal(comp.X), 2)) + "," + str(round(Decimal(comp.Y), 2)) + "," + \
                           (str(comp.Rotation).replace("\"", "")).replace("\n", "") + "," + comp.skip + ","
                output_file.write(out_line + "\n")

    def create_footprints_file(self):
        output_file = open(self.AltiumOutputFile.name.replace(".csv", "-FOOTPRINTS.csv"), "w")
        output_file.write("#Footprint,RotationCorrection\n")
        for f in self.footprints:
            output_file.write(str(f) + ",0.00\n")
        output_file.close()
        return output_file.name

    def create_parts_set(self):
        for component in self.components:
            part = component.Footprint + '/' + component.Comment
            if not (part in self.parts_names):
                self.parts_names.add(part)
                self.parts.append(Part(component.Footprint, component.Comment, part))
            else:
                for p in self.parts:
                    if part == p.part:
                        p.quantity += 1
                        break
        print("parts:" + str(len(self.parts))+"\n")

    def create_parts_file(self):
        output_file = open(self.AltiumOutputFile.name.replace(".csv", "-PARTS.csv"), "w")
        output_file.write("#Use find-n-replace tool in text editor for config feeders, unconfigurated will marked as 'Skip:Yes'\n")
        output_file.write("#Part,Feeder,Nozzle,qnt,Field 4 your comment c\n")
        for part in self.parts:
            output_file.write(part.Footprint + '\\' + part.Comment + ",0,0," + str(part.quantity) + ",\n")
        output_file.close()

    def make_angles_correction(self, correction_file_name):
        try:
            corr_file = open(correction_file_name, "r")
        except FileNotFoundError:
            print("No such correction file\n")
            return FileNotFoundError
        counter = 0
        for line in corr_file:
            if counter:
                footprint = line.split(',')[0]
                corr = line.split(',')[1]
                self.corrections.append(CorrectionForElement(str(footprint), float(corr)))
            counter += 1
        corrected = set()
        for component in self.components:
            for correction in self.corrections:
                if component.Footprint == correction.Footprint and correction.Correction != 0:
                    component.Rotation = str(float(correction.Correction) + float(component.Rotation))
                    component.Correction = correction.Correction
                    corrected.add(component.Footprint)
                    break
        print("angles corrected for: ")
        print(corrected)
        return 0

    def add_feeders(self, feeders_file_name):
        try:
            feeders_file = open(feeders_file_name, "r")
        except FileNotFoundError:
            print("No such feeders file\n")
            return FileNotFoundError
        feeders_confs = list()
        self.feeders_data_flag = True
        for line in feeders_file:
            if line[0] != '#':
                part = line.split(',')[0]
                feeder = int(line.split(',')[1])
                nozzle = int(line.split(',')[2])
                feeders_confs.append(Part(None, None, feeder=feeder, nozzle=nozzle, part=part))
        for component in self.components:
            part_str = component.Footprint + '\\' + component.Comment
            component.skip = 'Yes'
            component.feeder = self.default_feeder
            component.nozzle = self.default_nozzle
            for conf in feeders_confs:
                if part_str == conf.part:
                    if conf.feeder and conf.nozzle:
                        component.feeder = conf.feeder
                        component.nozzle = conf.nozzle
                        component.skip = 'No'
                    else:
                        pass
        return 0

    def move_angels_to_m180to180(self):
        for component in self.components:
            while float(component.Rotation) > 180.00:
                component.Rotation = str(float(component.Rotation) - 360.00)
            while float(component.Rotation) < -180.00:
                component.Rotation = str(float(component.Rotation) + 360.00)

    def flip_board(self):
        for comp in self.components:
            try:
                comp.X = str(float(comp.X) * (-1))
                comp.Rotation = str(360.00 - float(comp.Rotation))  #ЧЁ ТУТ БЫЛО??????
            except ValueError:
                print("===---*-*-*-*-*-*-=======")
                print(comp.Footprint)
                print("==========---*-*-*-*-*-*-")

    def mix_nozzles(self):
        nozzles_one_or_less = list()
        nozzles_other = list()
        nozzles_other_index = 0
        skiped_components = list()
        mixed_components = list()

        for comp in self.components:
            if comp.skip == 'Yes':
                skiped_components.append(comp)
            else:
                if comp.nozzle <= 1 :
                    nozzles_one_or_less.append(comp)
                else:
                    nozzles_other.append(comp)
        for comp_nozzle_1 in nozzles_one_or_less:
            mixed_components.append(comp_nozzle_1)
            if nozzles_other_index < len(nozzles_other):
                mixed_components.append(nozzles_other[nozzles_other_index])
                nozzles_other_index += 1
        print("Mixed %i lines\n"%(nozzles_other_index))
        while nozzles_other_index < len(nozzles_other):
            mixed_components.append(nozzles_other[nozzles_other_index])
            nozzles_other_index += 1
        for comp in skiped_components:
            mixed_components.append(comp)
        self.components = mixed_components
        return




    def __init__(self, file_name):
        try:
            self.AltiumOutputFile = open(file_name, "r")
        except FileNotFoundError:
            print("No such file\n")
            exit(-1)
        self.columns = Columns()
        self.footprints = set()
        self.components = list()
        self.parts_names = set()
        self.parts = list()
        self.corrections = list()
        self.make_component_list()
        self.feeders_data_flag = False
        self.default_feeder = 80
        self.default_nozzle = 1
        self.flip_flag = False
        self.firstChipPhysicalX = 0.0
        self.firstChipPhysicalY = 0.0
        self.columns = Columns()
        return

description = "Program for creating .CSV files for Neoden3V"
file_help = '*.csv file from Altium'
fp_help = "generate footprints list for making angle correction between Altium libs and position in tapes"
cl_help = "generate components list for convenient pairing components and feeders"
cf_help = "correct footprints rotation from file CF"
feed_help = "include components and feeders pairs from file PC"
top_help = "filter only top layer components"
bot_help = "filter only bot layer components"
flip_help = "flip board"
mix_help = "Mix component list between nozzles"
print_help = "Print result while generating"

def create_parser():
    arg_parser = argparse.ArgumentParser(description=description)
    arg_parser.add_argument('FILE', type=str, help=file_help)
    arg_parser.add_argument('-fp', action=argparse.BooleanOptionalAction, type=bool, default=False, help=fp_help)
    arg_parser.add_argument('-cl', action=argparse.BooleanOptionalAction, type=bool, default=False, help=cl_help)
    arg_parser.add_argument('-top', action=argparse.BooleanOptionalAction, type=bool, default=False, help=top_help)
    arg_parser.add_argument('-bot', action=argparse.BooleanOptionalAction, type=bool, default=False, help=bot_help)
    arg_parser.add_argument('-flip', action=argparse.BooleanOptionalAction, type=bool, default=False, help=flip_help)
    arg_parser.add_argument('-mix', action=argparse.BooleanOptionalAction, type=bool, default=False, help=mix_help)
    arg_parser.add_argument('-print', action=argparse.BooleanOptionalAction, type=bool, default=False, help=print_help)
    arg_parser.add_argument('-cf', type=str, help=cf_help)
    arg_parser.add_argument('-feed', type=str, help=feed_help)
    return arg_parser


argc = len(sys.argv)
parser = create_parser()
args = parser.parse_args(sys.argv[1:])
print(args)

print("*****************")

converter = NeoDenConverter(args.FILE)
no_output_generate_flag = False

if args.fp:
    frame = converter.create_footprints_file()
    print("template of footprints angle correction file is generated(" + frame + ")\n")
    no_output_generate_flag = True
if args.cl:
    converter.create_parts_set()
    converter.create_parts_file()
    no_output_generate_flag = True

if no_output_generate_flag:
    exit(0)

if args.flip:
    converter.flip_board()


if args.cf:
    if 0 == converter.make_angles_correction(args.cf):
        print("successful correction\n")
    else:
        exit(0)

if args.feed:
    if 0 == converter.add_feeders(args.feed):
        print("successful feeders config\n")
    else:
        exit(0)

if args.top:
    layer_flag = 'TopLayer'
else:
    if args.bot:
        layer_flag = 'BottomLayer'
    else:
        layer_flag = None

converter.move_angels_to_m180to180()

converter.get_distances_from_first_chip()
converter.firstChipPhysicalX = float(
    input("Enter the machine X coordinate of component " + converter.components[0].Designator + " : "))
converter.firstChipPhysicalY = float(
    input("Enter the machine Y coordinate of component " + converter.components[0].Designator + " : "))
converter.apply_machine_positions_2_components()

if args.mix:
    converter.mix_nozzles()

if args.print:
    print("----------------")
    for comp in converter.components:
        strout = "%s,\t, row: %f,\t corr %s,\t rot %f \t %s \t Nzl %s" % (comp.Designator, float(comp.RawRotation),
                                                                          comp.Correction, float(comp.Rotation),
                                                                          comp.Footprint, comp.nozzle)
        print(strout)
    print("----------------")

converter.create_output_file(layer_flag)
