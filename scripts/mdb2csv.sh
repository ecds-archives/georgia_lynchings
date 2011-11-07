#!/bin/bash

# DESCRIPTION: This script converts the Georgia Lynchings access mdb file 
# into csv files for each table.

# USAGE: convert_mdb_to_csv.sh <path to access mdb file> <output directory>
# EXAMPLE: ./convert_mdb_to_csv.sh ../lynching_data/galyn_no_pw.mdb ../csv

# Usage Message Function
usage ()
{  
  echo " " 
  echo $errmsg
  echo " "  
  echo "usage: convert_mdb_to_csv.sh <path to access mdb file> <output directory>" 
  echo " "   
}

# Validate input parameters
if [ $# -ne 2 ] ; then errmsg="Error: Incorrect number of arguments."; usage; exit 1;
elif [ ! -f $1 ] ; then errmsg="Error: \"${1}\" <path to access mdb file> not found"; usage; exit 1;
elif [ ! -d $2 ] ; then errmsg="Error: \"${2}\" <output directory> not found"; usage; exit 1;
fi

hash mdb-export 2>&- || { echo -e >&2 "\nError: This script requires mdbtools but it's not installed.\nRun 'sudo apt-get install mdbtools'\nAborting."; exit 1; }

mdb-export $1 data:Complex > $2/data_Complex.csv
mdb-export $1 data:Simplex > $2/data_Simplex.csv
mdb-export $1 data:SimplexDate > $2/data_SimplexDate.csv
mdb-export $1 data:SimplexText > $2/data_SimplexText.csv
mdb-export $1 data:TempTranslatorCU > $2/data_TempTranslatorCU.csv
mdb-export $1 data:VCommentArchive > $2/data_VCommentArchive.csv
mdb-export $1 data:xref:AnyComplex-Complex > $2/data_xref_AnyComplex-Complex.csv
mdb-export $1 data:xref:comment-complex > $2/data_xref_comment-complex.csv
mdb-export $1 data:xref:Comment-Document > $2/data_xref_Comment-Document.csv
mdb-export $1 data:xref:Comment-Simplex > $2/data_xref_Comment-Simplex.csv
mdb-export $1 data:xref:Complex-Document > $2/data_xref_Complex-Document.csv
mdb-export $1 data:xref:Simplex-Complex > $2/data_xref_Simplex-Complex.csv
mdb-export $1 data:xref:Simplex-Document > $2/data_xref_Simplex-Document.csv
mdb-export $1 data:xref:Simplex-Simplex-Document > $2/data_xref_Simplex-Simplex-Document.csv
mdb-export $1 data:xref:VComment > $2/data_xref_VComment.csv
mdb-export $1 data:xref:VComment-Document > $2/data_xref_VComment-Document.csv
mdb-export $1 setup:Complex > $2/setup_Complex.csv
mdb-export $1 setup:Document > $2/setup_Document.csv
mdb-export $1 setup:Simplex > $2/setup_Simplex.csv
mdb-export $1 setup:xref:Complex-Complex > $2/setup_xref_Complex-Complex.csv
mdb-export $1 setup:xref:Simplex-Complex > $2/setup_xref_Simplex-Complex.csv
mdb-export $1 setup:xref:Simplex-Document > $2/setup_xref_Simplex-Document.csv
mdb-export $1 usertable:apprehension > $2/usertable_apprehension.csv
mdb-export $1 usertable:control > $2/usertable_control.csv
mdb-export $1 usertable:eql_f0 > $2/usertable_eql_f0.csv
mdb-export $1 usertable:Network > $2/usertable_Network.csv
mdb-export $1 "usertable:Network coercion" > $2/usertable_Network-coercion.csv
mdb-export $1 "usertable:Network sexual violence" > $2/usertable_Network-sexual-violence.csv
mdb-export $1 "usertable:Network viol test" > $2/usertablst.csv
mdb-export $1 "usertable:Network violence" > $2/usertable_Network-violence.csv
mdb-export $1 usertable:SAO > $2/usertable_SAO.csv
mdb-export $1 usertable:violence > $2/usertable_violence.csv
mdb-export $1 "usertable:violence people" > $2/usertable_violence_people.csv
mdb-export $1 usertable:violence_2 > $2/usertable_violence_2.csv
mdb-export $1 utility:Bookmarks > $2/utility_Bookmarks.csv
mdb-export $1 utility:Reminders > $2/utility_Reminders.csv
mdb-export $1 utility:Scripts > $2/utility_Scripts.csv
mdb-export $1 utility:Security > $2/utility_Security.csv
mdb-export $1 utility:Settings > $2/utility_Settings.csv
mdb-export $1 data:Document > $2/data_Document.csv
mdb-export $1 data:SimplexNumber > $2/data_SimplexNumber.csv
mdb-export $1 data:xref:Complex-Complex > $2/data_xref_Complex-Complex.csv
