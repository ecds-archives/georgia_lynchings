#!/usr/bin/env python

# Run with no args for usage instructions
#
# Notes:
#  - will probably insert duplicate records if you load the same file twice
#  - assumes that the number of fields in the header row is the same
#    as the number of columns in the rest of the file and in the database
#  - assumes the column order is the same in the file and in the database
#
# Speed: ~ 1s/MB
# 

# Drop all tables from existing database
# mysql -u deploy --password=yolped galyn_trunk -e "show tables" | grep -v Tables_in | grep -v "+" | gawk '{print "drop table " $1 ";"}' | mysql -u deploy --password=yolped galyn_trunk
# Create all tables
# mysql -u deploy --password=yolped galyn_trunk < schema_data.sql

import sys
import MySQLdb
import csv
import os

def main(user="deploy", passwd="yolped", db="galyn_trunk", csv_path="../lynching_data/"):
  
  print "\ndb=[%s] csv_path=[%s]\n" % (db, csv_path)   

  try:
    conn = getconn(user, db, passwd)
  except MySQLdb.Error, e:
    print "Error %d: %s" % (e.args[0], e.args[1])
    sys.exit (1)
  
  cursor = conn.cursor()
    
  # load a list of csv files
  csv_files = os.listdir(csv_path);
    
  # traverse the list of csv files
  for csvfile in csv_files:    
    (table, ext) = os.path.splitext(csvfile) 
    if (ext=='.csv'):
      print "\nLoad table[%s] file=[%s]" % (table, os.path.join(csv_path, csvfile))    
      loadcsv(cursor, table, os.path.join(csv_path, csvfile))    

  cursor.close()
  conn.close()

def getconn(user, db, passwd=""):
  conn = MySQLdb.connect(host = "localhost",
			 user = user,
			 passwd = passwd,
			 db = db)
  return conn

def nullify(L):
  """Convert empty strings in the given list to None."""

  # helper function
  def f(x):
      if(x == ""):
	  return None
      else:
	  return x
      
  return [f(x) for x in L]

def loadcsv(cursor, table, filename):

  """
  Open a csv file and load it into a sql table.
  Assumptions:
   - the first line in the file is a header
  """

  f = csv.reader(open(filename))
  
  header = f.next()
  numfields = len(header)

  query = buildInsertCmd(table, numfields)

  for line in f:
      vals = nullify(line)
      cursor.execute(query, vals)

  return

def buildInsertCmd(table, numfields):

  """
  Create a query string with the given table name and the right
  number of format placeholders.

  example:
  >>> buildInsertCmd("foo", 3)
  'insert into foo values (%s, %s, %s)' 
  """
  assert(numfields > 0)
  placeholders = (numfields-1) * "%s, " + "%s"
  query = ("insert into %s" % table) + (" values (%s)" % placeholders)
  return query

if __name__ == '__main__':
  # commandline execution
  
  args = sys.argv[1:]
  if(len(args) < 4):
      print "error: arguments: user pw dbname csvdir"
      sys.exit(1)

  main(*args)
