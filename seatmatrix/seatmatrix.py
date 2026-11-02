import csv
import sys
import random
from itertools import product
import bisect


def header_names():
    castes = ['OC', 'BC-A', 'BC-B', 'BC-C', 'BC-D', 'BC-E', 'SC-1', 'SC-2', 'SC-3', 'ST']
    splcats = ['', 'PWD', 'NCC', 'CAP', 'SG', 'SCG']
    categories = ['GEN', 'GIRLS']
    regions = ['UR', 'AU', 'SVU']
    combinations = product(castes, splcats, categories, regions)
    names = ['_'.join(combo).replace('__', '_') for combo in combinations]
    minorities = ['MUS', 'CHR']
    names.extend(['_'.join(combo).replace('__', '_') for combo in product(minorities, categories, regions)])
    names.extend(['_'.join(combo).replace('__', '_') for combo in product(['EWS'], splcats[:2], categories, regions)])
    return sorted(names)

def read_input_csv(input_csv):
    with open(input_csv, 'r') as infile:
        reader = csv.DictReader(infile)
        header = reader.fieldnames
        rows = list(reader)
        for row in rows:
            row['Convenor'] = int(row['Convenor'])
            row['EWS'] = int(row['EWS'])
    return header, rows

def save_output_csv(output_csv, header, rows):
    with open(output_csv, 'w', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=header, restval=0)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

def initialize_seat_matrix(rows):
    for row in rows:
        if row['Category'] == 'MUS':
            row['MUS_GEN_UR'] = row.get('Convenor')
        elif row['Category'] == 'MUSW':
            row['MUS_GIRLS_UR'] = row.get('Convenor')
        elif row['Category'] == 'CHR':
            row['CHR_GEN_UR'] = row.get('Convenor')
        elif row['Category'] == 'CHRW':
            row['CHR_GIRLS_UR'] = row.get('Convenor')
        elif row['Category'][-1] == 'W':
            row['OC_GIRLS_UR'] = row.get('Convenor')
            row['EWS_GIRLS_UR'] = row.get('EWS')
        else:
            row['OC_GEN_UR'] = row.get('Convenor')
            row['EWS_GEN_UR'] = row.get('EWS')
    return rows

def move_seats_ur_to_region(rows, from_category, percentage):
    # Implementation for moving seats between categories
    seats_remaining = 0
    to_category_prefix = from_category[:-3]  # Remove the last 3 characters to get the prefix
    for row in rows:
        if from_category not in row:
            continue
        seats_remaining += row[from_category] * percentage
        seats_to_move = seats_remaining // 1  # Convert to integer
        seats_remaining -= seats_to_move
        row[from_category] -= seats_to_move
        row[f'{to_category_prefix}_{'SVU' if row["Region"] == 'SVU' else 'AU'}'] = seats_to_move

def move_seats(rows, from_category, to_category, percentage, statewide=False):
    # Implementation for moving seats between categories
    seats_remaining = 0
    for row in rows:
        if statewide and row['Region'] != 'SW':
            continue
        if from_category not in row:
                    continue
        seats_remaining += row[from_category] * percentage
        seats_to_move = seats_remaining // 1  # Convert to integer
        seats_remaining -= seats_to_move
        row[from_category] -= seats_to_move
        row[to_category] = seats_to_move

def move_seats_bulk(rows, from_category, to_category, percentage):
    for comm in ['GEN', 'GIRLS']:
        for reg in ['AU', 'SVU', 'UR']:
            move_seats(rows, f'{from_category}_{comm}_{reg}', f'{to_category}_{comm}_{reg}', percentage)

def shuffle_with_index(lst):
    """Shuffle list and return the permutation indices."""
    indices = list(range(len(lst)))
    random.shuffle(indices)
    shuffled = [lst[i] for i in indices]
    return shuffled, indices

def restore_from_indices(shuffled, indices):
    """Restore original list using recorded indices."""
    restored = [None] * len(shuffled)
    for i, idx in enumerate(indices):
        restored[idx] = shuffled[i]
    return restored

def move_seats_special_category(rows, from_prefix, to_prefix, percentage):
    spl_forward = 0
    for comm in ['GEN', 'GIRLS']:
        for reg in ['AU', 'SVU', 'UR']:
            from_category = f'{from_prefix}_{comm}_{reg}'
            to_category = f'{from_prefix}_{to_prefix}_{comm}_{reg}'
            total_seats = sum([row[from_category] for row in rows if from_category in row and row[from_category] > 0])
            spl_forward += total_seats * percentage
            spl_seats = spl_forward // 1  # percentage of total seats, rounded down
            spl_forward -= spl_seats
            ratio = spl_seats / total_seats
            move_seats(rows, from_category, to_category, ratio)

def main(argv):
    if len(argv) != 3:
        print("Usage: python seatmatrix.py <input_csv> <output_csv>")
        return 1

    input_csv, output_csv = argv[1], argv[2]

    header, rows = read_input_csv(input_csv)
    header = header + header_names()

    # copy convenor and ews quotas to the corresponding reservation columns
    initialize_seat_matrix(rows)

    rows, indices = shuffle_with_index(rows)

    # =====================================================
    # 85%, 15% split of seats between GEN and UR categories
    # move 85% seats from UR to GEN/GIRLS categories
    # =====================================================
    for from_category in ['OC_GEN_UR', 'OC_GIRLS_UR', 'MUS_GEN_UR', 'MUS_GIRLS_UR', 'CHR_GEN_UR', 'CHR_GIRLS_UR', 'EWS_GEN_UR', 'EWS_GIRLS_UR']:
        move_seats_ur_to_region(rows, from_category, 0.85)

    # =========================================================================================
    # 65.62%, 34.38% split of seats between AU and SVU categories for statewide institutes
    # move 85% seats from OC_(GEN/GIRLS)_AU to OC_(GEN/GIRLS)_SVU categories when Region = 'SW'
    # =========================================================================================
    for from_category, to_category in [('OC_GEN_AU', 'OC_GEN_SVU'), ('OC_GIRLS_AU', 'OC_GIRLS_SVU')]:
        move_seats(rows, from_category, to_category, 0.3438, True)

    # ================================================================
    # 2/3 (GEN), 1/3 (GIRLS) split across (OC/MUS/CHR)_GEN_(AU/SVU/UR)
    # ================================================================
    for comm in ['OC', 'MUS', 'CHR', 'EWS']:
        for reg in ['AU', 'SVU', 'UR']:
            move_seats(rows, f'{comm}_GEN_{reg}', f'{comm}_GIRLS_{reg}', 0.3333)

    # ===================================================================
    # 50% (OC), 50% (REMAINING) split across (OC)_{GEN/GIRLS}_(AU/SVU/UR)
    # ===================================================================
    move_seats_bulk(rows, 'OC', 'BC-A', 0.5)

    # =====================================================================
    # 29% (BC), 21% (REMAINING) split across (BC-A)_{GEN/GIRLS}_(AU/SVU/UR)
    # 58%       42%
    # =====================================================================
    move_seats_bulk(rows, 'BC-A', 'SC-1', 0.42)

    # =======================================================================
    # 15% (SC), 6% (REMAINING-ST) split across (SC-1)_{GEN/GIRLS}_(AU/SVU/UR)
    # 71.43%    28.57%
    # =======================================================================
    move_seats_bulk(rows, 'SC-1', 'ST', 0.2857)

    # ======================================================================
    # 7% (BC-A), 22% (REMAINING) split across (BC-A)_{GEN/GIRLS}_(AU/SVU/UR)
    # 24.14%     75.86%
    # ======================================================================
    move_seats_bulk(rows, 'BC-A', 'BC-B', 0.7586)

    # =======================================================================
    # 10% (BC-B), 12% (REMAINING) split across (BC-B)_{GEN/GIRLS}_(AU/SVU/UR)
    # 45.45%      54.55%
    # =======================================================================
    move_seats_bulk(rows, 'BC-B', 'BC-C', 0.5455)

    # ======================================================================
    # 1% (BC-C), 11% (REMAINING) split across (BC-C)_{GEN/GIRLS}_(AU/SVU/UR)
    # 8.33%      91.67%
    # ======================================================================
    move_seats_bulk(rows, 'BC-C', 'BC-D', 0.9167)

    # =====================================================================
    # 7% (BC-D), 4% (REMAINING) split across (BC-D)_{GEN/GIRLS}_(AU/SVU/UR)
    # 63.64%     36.36%
    # =====================================================================
    move_seats_bulk(rows, 'BC-D', 'BC-E', 0.3636)

    # ======================================================================
    # 1% (SC-1), 14% (REMAINING) split across (BC-A)_{GEN/GIRLS}_(AU/SVU/UR)
    # 6.67%      93.33%
    # ======================================================================
    move_seats_bulk(rows, 'SC-1', 'SC-2', 0.9333)

    # =========================================================================
    # 6.5% (SC-2), 7.5% (REMAINING) split across (BC-A)_{GEN/GIRLS}_(AU/SVU/UR)
    # 46.43%       53.57%
    # =========================================================================
    move_seats_bulk(rows, 'SC-2', 'SC-3', 0.5357)

    # ======================================================
    # Special Categories (Horizontal reservations)
    # 5% (PWD), 2% (CAP), 1% NCC, 0.5% SG 0.5% SCG
    # split across (OC/BC-X/SC-X/ST)_{GEN/GIRLS}_(AU/SVU/UR)
    # for EWS only PWD is applicable
    # ======================================================
    # 9% to PWD
    for from_prefix in ['OC', 'BC-A', 'BC-B', 'BC-C', 'BC-D', 'BC-E', 'SC-1', 'SC-2', 'SC-3', 'ST', 'EWS']:
        move_seats_special_category(rows, from_prefix, 'PWD', 0.09)

    # 4% to CAP
    for from_prefix in ['OC', 'BC-A', 'BC-B', 'BC-C', 'BC-D', 'BC-E', 'SC-1', 'SC-2', 'SC-3', 'ST']:
        move_seats_bulk(rows, f'{from_prefix}_PWD', f'{from_prefix}_CAP', 0.4444)

    # 2% to NCC
    for from_prefix in ['OC', 'BC-A', 'BC-B', 'BC-C', 'BC-D', 'BC-E', 'SC-1', 'SC-2', 'SC-3', 'ST']:
        move_seats_bulk(rows, f'{from_prefix}_CAP', f'{from_prefix}_NCC', 0.5)

    # 1% to SG
    for from_prefix in ['OC', 'BC-A', 'BC-B', 'BC-C', 'BC-D', 'BC-E', 'SC-1', 'SC-2', 'SC-3', 'ST']:
        move_seats_bulk(rows, f'{from_prefix}_NCC', f'{from_prefix}_SG', 0.5)

    # 0.5% to SCG
    for from_prefix in ['OC', 'BC-A', 'BC-B', 'BC-C', 'BC-D', 'BC-E', 'SC-1', 'SC-2', 'SC-3', 'ST']:
        move_seats_bulk(rows, f'{from_prefix}_SG', f'{from_prefix}_SCG', 0.5)

    rows = restore_from_indices(rows, indices)
    save_output_csv(output_csv, header, rows)

if __name__ == "__main__":
    sys.exit(main(sys.argv))
