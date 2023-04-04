#!/usr/bin/python3
import csv
import argparse

# create an argument parser to accept the file path argument
parser = argparse.ArgumentParser()
parser.add_argument("file_path", help="path to CSV file")
parser.add_argument("--inputs", action="store_true", help="print input elements too")
parser.add_argument("--output_file", default='variables.txt', help="path to output file")
args = parser.parse_args()

# open the CSV file and read its contents
with open(args.file_path, newline='') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=';')
    # open the output file
    with open(args.output_file, "w") as output_file:
        # iterate over each row in the CSV file
        for row in reader:
            # check if the "IO-Type" column is "Output" and name is not empty
            if row["IO-Type"] == "Output" and row["Name"].strip() != "":
                # write the "Name" column value to the output file
                output_file.write(row["Name"] + "\n")
            elif args.inputs and row["IO-Type"] == "Input" and row["Name"].strip() != "":
                # optionally write input elements to the output file
                output_file.write(row["Name"] + "\n")
