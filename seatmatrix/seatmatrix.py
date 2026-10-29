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

def get_region_category_dict(regions_path):
    regions = {}
    with open(regions_path, newline="", encoding="utf-8-sig") as fin:
        reader = csv.reader(fin)
        header = [key.lower() for key in next(reader)]
        if header != ["category", "region", "instcode"]:
            print(f"Invalid header in {regions_path}. Expected ['category', 'region', 'instcode'], got {header}", file=sys.stderr)
            return None

        for row in reader:
            if len(row) != 3:
                print(f"Invalid row in {regions_path}: {row}. Expected 3 columns.", file=sys.stderr)
                return None

            cat, reg, inst = row
            key = (reg.strip(), cat.strip())
            if regions.get(key) is None:
                regions[key] = [inst.strip()]
            else:
                regions[key].append(inst.strip())

    return regions

def get_inst_wise_prgms_and_counts(in_path):
    inst_prgms = {}
    inst_prgm_counts = {}

    with open(in_path, newline="", encoding="utf-8-sig") as fin:
        reader = csv.reader(fin)
        header = [key.lower() for key in next(reader)]
        if header != ["instcode", "programcode", "convener", "ews"]:
            print(f"Invalid header in {in_path}. Expected ['instcode', 'programcode', 'convener', 'ews'], got {header}", file=sys.stderr)
            return None

        for row in reader:
            if len(row) != 4:
                print(f"Invalid row in {in_path}: {row}. Expected 4 columns.", file=sys.stderr)
                return None

            inst, pc, cq, ews = row
            key1 = inst.strip()
            key2 = pc.strip()

            if inst_prgms.get(key1) is None:
                inst_prgms[key1] = [key2]
            else:
                inst_prgms[key1].append(key2)

            inst_prgm_counts[(key1, key2)] = [int(cq), int(ews)]

    return inst_prgms, inst_prgm_counts

def distribute_85_15(prgm_inst_map, header_names_list, inst_prgm_counts, key, fromcat):
    for prg, institutes in prgm_inst_map.items():
        random.shuffle(institutes)
        
        unr_forward = 0
        sw_forward = 0
        for inst in institutes:
            seats = inst_prgm_counts[(inst, prg)][0 if fromcat == 'OC' else 1]
            unr_forward += seats * 0.15
            unr_seats = int(unr_forward) 
            unr_forward -= unr_seats
            au_svu_seats = seats - unr_seats
            if unr_forward > 0:
                au_svu_seats -= 1
                unr_seats += 1
                unr_forward -= 1
                
            if key[1][:3] == 'GEN':
                unr_index = bisect.bisect_left(header_names_list, f"{fromcat}_{'GEN' if key[1] == 'GEN' else 'GIRLS'}_UR") + 2
                au_svu_index = bisect.bisect_left(header_names_list, f"{fromcat}_{'GEN' if key[1] == 'GEN' else 'GIRLS'}_{key[0]}") + 2
                inst_prgm_counts[(inst, prg)][unr_index] = unr_seats
                inst_prgm_counts[(inst, prg)][au_svu_index] = au_svu_seats
            elif fromcat == 'OC' and key[1][:3] in ['MUS', 'CHR']:
                unr_index = bisect.bisect_left(header_names_list, f"{key[1][:3]}_{'GEN' if key[1] in ['MUS', 'CHR'] else 'GIRLS'}_UR") + 2
                au_svu_index = bisect.bisect_left(header_names_list, f"{key[1][:3]}_{'GEN' if key[1] in ['MUS', 'CHR'] else 'GIRLS'}_{key[0]}") + 2
                inst_prgm_counts[(inst, prg)][unr_index] = unr_seats
                inst_prgm_counts[(inst, prg)][au_svu_index] = au_svu_seats
            elif key[1][:3] == 'SWI':
                # AU (65.62%), SVU (34.38%)
                sw_forward += au_svu_seats * 0.3438
                svu_seats = int(sw_forward) 
                sw_forward -= svu_seats
                au_seats = au_svu_seats - svu_seats
                if sw_forward > 0:
                    au_seats -= 1
                    svu_seats += 1
                    sw_forward -= 1
                unr_index = bisect.bisect_left(header_names_list, f"{fromcat}_{'GEN' if key[1] == 'SWI' else 'GIRLS'}_UR") + 2
                au_index = bisect.bisect_left(header_names_list, f"{fromcat}_{'GEN' if key[1] == 'SWI' else 'GIRLS'}_AU") + 2
                svu_index = bisect.bisect_left(header_names_list, f"{fromcat}_{'GEN' if key[1] == 'SWI' else 'GIRLS'}_SVU") + 2
                inst_prgm_counts[(inst, prg)][unr_index] = unr_seats
                inst_prgm_counts[(inst, prg)][au_index] = au_seats
                inst_prgm_counts[(inst, prg)][svu_index] = svu_seats
            else:
                continue

def distribute_gen_girls(prgm_inst_map, header_names_list, inst_prgm_counts):
    for prg, institutes in prgm_inst_map.items():
        for reg in ['AU', 'SVU', 'UR']:
            for comm in ['OC', 'MUS', 'CHR', 'EWS']:
                source_index = bisect.bisect_left(header_names_list, f"{comm}_GEN_{reg}") + 2
                random.shuffle(institutes)

                girls_forward = 0
                for inst in institutes:
                    seats = inst_prgm_counts[(inst, prg)][source_index]
                    if seats == 0:
                        continue
                    girls_forward += seats / 3
                    girls_seats = int(girls_forward)
                    girls_forward -= girls_seats
                    if girls_forward > 0:
                        girls_seats += 1
                        girls_forward -= 1

                    girls_index = bisect.bisect_left(header_names_list, f"{comm}_GIRLS_{reg}") + 2
                    inst_prgm_counts[(inst, prg)][source_index] -= girls_seats
                    inst_prgm_counts[(inst, prg)][girls_index] = girls_seats

def distribute_between_two_columns(prgm_inst_map, header_names_list, inst_prgm_counts, fromcat, tocat, rempercent):
    for prg, institutes in prgm_inst_map.items():
        for reg in ['AU', 'SVU', 'UR']:
            for comm in ['GEN', 'GIRLS']:
                source_index = bisect.bisect_left(header_names_list, f"{fromcat}_{comm}_{reg}") + 2
                random.shuffle(institutes)
                
                rem_forward = 0
                for inst in institutes:
                    seats = inst_prgm_counts[(inst, prg)][source_index]
                    if seats == 0:
                        continue
                    rem_forward += seats * rempercent
                    rem_seats = int(rem_forward)
                    rem_forward -= rem_seats
                    if rem_forward > 0:
                        rem_seats += 1
                        rem_forward -= 1

                    girls_index = bisect.bisect_left(header_names_list, f"{tocat}_{comm}_{reg}") + 2
                    inst_prgm_counts[(inst, prg)][source_index] -= rem_seats
                    inst_prgm_counts[(inst, prg)][girls_index] = rem_seats

def main(argv):
    if len(argv) < 4:
        print("Usage: python seat_matrix_generator.py input.csv output.csv regions.csv", file=sys.stderr)
        return 1

    in_path, out_path, regions_path = argv[1], argv[2], argv[3]

    regions = get_region_category_dict(regions_path)
    if regions is None:
        print(f"Error processing regions file: {regions_path}", file=sys.stderr)
        return 1

    inst_prgms, inst_prgm_counts = get_inst_wise_prgms_and_counts(in_path)
    if inst_prgms is None or inst_prgm_counts is None:
        print(f"Error processing input file: {in_path}", file=sys.stderr)
        return 1

    header_names_list = header_names()

    for inst, prg in inst_prgm_counts:
        inst_prgm_counts[(inst, prg)].extend([0] * len(header_names_list))

    for key, inst_list in regions.items():
        print(key)

        for inst in inst_list:
            if inst not in inst_prgms:
                print(f"Warning: Institution {inst} in regions file not found in input file.", file=sys.stderr)
                return 1

        prgm_inst_map = {}
        for inst in inst_list:
            for prg in inst_prgms[inst]:
                if prg in prgm_inst_map:
                    prgm_inst_map[prg].append(inst)
                else:
                    prgm_inst_map[prg] = [inst]

        # random.shuffle(prgm_inst_map)

        # =============================================================
        # 85% (AU/SVU), 15% (UNR) split for each program's institutions
        # =============================================================
        distribute_85_15(prgm_inst_map, header_names_list, inst_prgm_counts, key, 'OC')

        # =================================================================
        # 85% (AU/SVU), 15% (UNR) split for each program's institutions-EWS
        # =================================================================
        distribute_85_15(prgm_inst_map, header_names_list, inst_prgm_counts, key, 'EWS')
                
        # =================================================================================================
        # 2/3 (GEN), 1/3 (GIRLS) split across (OC/MUS/CHR)_GEN_(AU/SVU/UR) where the allocation is non-zero-ALL
        # =================================================================================================
        distribute_gen_girls(prgm_inst_map, header_names_list, inst_prgm_counts)

        # ====================================================================================================
        # 50% (OC), 50% (REMAINING) split across (OC)_{GEN/GIRLS}_(AU/SVU/UR) where the allocation is non-zero
        # ====================================================================================================
        distribute_between_two_columns(prgm_inst_map, header_names_list, inst_prgm_counts, 'OC', 'BC-A', 0.5)

        # ======================================================================================================
        # 29% (BC), 21% (REMAINING) split across (BC-A)_{GEN/GIRLS}_(AU/SVU/UR) where the allocation is non-zero
        # 58%       42%
        # ======================================================================================================
        distribute_between_two_columns(prgm_inst_map, header_names_list, inst_prgm_counts, 'BC-A', 'SC-1', 0.42)

        # ========================================================================================================
        # 15% (SC), 6% (REMAINING-ST) split across (SC-1)_{GEN/GIRLS}_(AU/SVU/UR) where the allocation is non-zero
        # 71.43%    28.57%
        # ========================================================================================================
        distribute_between_two_columns(prgm_inst_map, header_names_list, inst_prgm_counts, 'SC-1', 'ST', 0.2857)

        # =======================================================================================================
        # 7% (BC-A), 22% (REMAINING) split across (BC-A)_{GEN/GIRLS}_(AU/SVU/UR) where the allocation is non-zero
        # 24.14%     75.86%
        # =======================================================================================================
        distribute_between_two_columns(prgm_inst_map, header_names_list, inst_prgm_counts, 'BC-A', 'BC-B', 0.7586)

        # ========================================================================================================
        # 10% (BC-B), 12% (REMAINING) split across (BC-B)_{GEN/GIRLS}_(AU/SVU/UR) where the allocation is non-zero
        # 45.45%      54.55%
        # ========================================================================================================
        distribute_between_two_columns(prgm_inst_map, header_names_list, inst_prgm_counts, 'BC-B', 'BC-C', 0.5455)

        # ======================================================================================================
        # 1% (BC-C), 11% (REMAINING) split across (BC-C)_{GEN/GIRLS}_(AU/SVU/UR) where the allocation is non-zero
        # 8.33%      91.67%
        # ======================================================================================================
        distribute_between_two_columns(prgm_inst_map, header_names_list, inst_prgm_counts, 'BC-C', 'BC-D', 0.9167)

        # ======================================================================================================
        # 7% (BC-D), 4% (REMAINING) split across (BC-D)_{GEN/GIRLS}_(AU/SVU/UR) where the allocation is non-zero
        # 63.64%     36.36%
        # ======================================================================================================
        distribute_between_two_columns(prgm_inst_map, header_names_list, inst_prgm_counts, 'BC-D', 'BC-E', 0.3636)

        # ======================================================================================================
        # 1% (SC-1), 14% (REMAINING) split across (BC-A)_{GEN/GIRLS}_(AU/SVU/UR) where the allocation is non-zero
        # 6.67%      93.33%
        # ======================================================================================================
        distribute_between_two_columns(prgm_inst_map, header_names_list, inst_prgm_counts, 'SC-1', 'SC-2', 0.9333)

        # ======================================================================================================
        # 6.5% (SC-2), 7.5% (REMAINING) split across (BC-A)_{GEN/GIRLS}_(AU/SVU/UR) where the allocation is non-zero
        # 46.43%       53.57%
        # ======================================================================================================
        distribute_between_two_columns(prgm_inst_map, header_names_list, inst_prgm_counts, 'SC-2', 'SC-3', 0.5357)

    with open(out_path, "w", newline="", encoding="utf-8") as fout:
        fout.write("Region,Category,InstCode,ProgramCode,Convenor,EWS," + ",".join(header_names()) + "\r\n")
        for key, inst_list in regions.items():
            for inst in inst_list:
                for prg in inst_prgms[inst]:
                    counts = inst_prgm_counts[(inst, prg)]
            # for (inst, prg), counts in inst_prgm_counts.items():
                    fout.write(f"{key[0]},{key[1]},{inst},{prg}," + ",".join(map(str, counts)) + "\r\n")
    
if __name__ == "__main__":
    sys.exit(main(sys.argv))