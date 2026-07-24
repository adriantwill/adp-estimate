from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SOURCE_DATA_DIR = DATA_DIR / "source"
CLEAN_DATA_DIR = DATA_DIR / "clean"

PFF_DIR = SOURCE_DATA_DIR / "pff"
PROS_BB_ADP_DIR = SOURCE_DATA_DIR / "pros_bb_adp"
PFF_RECEIVING_DIR = PFF_DIR / "pff_recieving"
PFF_PASSING_DIR = PFF_DIR / "pff_passing"
RECEIVING_FINISH_DIR = PFF_DIR / "recieving_finish"
PASSING_FINISH_DIR = PFF_DIR / "passing_finish"

MERGED_WR_CSV = CLEAN_DATA_DIR / "merged_wr.csv"
MERGED_QB_CSV = CLEAN_DATA_DIR / "merged_qb.csv"
AVERAGE_CSV = CLEAN_DATA_DIR / "average.csv"
