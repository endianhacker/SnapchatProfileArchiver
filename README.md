# SnapchatProfileArchiver
Archive snapchat profiles

# Usage
python archiver.py -u <username> --write_json 1


usage: SnapchatArchiver [-h] -u USER [--write_json WRITE_JSON] [--output_dir OUTPUT_DIR]
                        [--related_archive RELATED_ARCHIVE] [--deep_archive DEEP_ARCHIVE]

OSINT archive snapchat user

options:
  -h, --help            show this help message and exit
  
  -u USER, --user USER  target username
  
  --write_json WRITE_JSON
                        json output
                        
  --output_dir OUTPUT_DIR
                        change the output directory
                        
  --related_archive RELATED_ARCHIVE
                        archive related accounts, too.
                        
  --deep_archive DEEP_ARCHIVE
                        recursive archiving related accounts, WARNING EXPERIMENTAL, MAY RUN FOR AN EXTREMELY LONG TIME
                        
