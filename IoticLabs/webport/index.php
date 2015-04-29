<?php

/* CONFIGURATION */

$DATA_FILE = "data.txt";
//$KEY       = "1224";

function doError($msg) // param error number?
{
  /* Response */
  //TODO send back HTTP 500 server error?
  print("ERROR: $msg");
}

function isKeyValid($key)
{
  return true; //TODO
}


function doPut($query)
{
  global $DATA_FILE;
  /* Request */
  //TODO check key validity from header token
  //Throw error if invalid

  // new data comes in the POST body
  $rawInput = fopen('php://input', 'r');
  $dataFile = fopen(strval($query['id']). "_" . $DATA_FILE, 'a');

  /* write all data in append mode to the data file */
  stream_copy_to_stream($rawInput, $dataFile);

  fclose($dataFile);
  fclose($rawInput);

  /* Response */
  print("OK POSTed");
}

function doGet($query)
{
  global $DATA_FILE;

  $fileName = strval($query['id']). "_" . $DATA_FILE;
  $dataFile = fopen($fileName, 'r') or die("These are not the droids you are looking for!");
  echo fread($dataFile,filesize($fileName));
  fclose($dataFile);

}

function doDelete($query)
{
  global $DATA_FILE;
  /* Request */
  //TODO check key validity from header token
  //Throw error if invalid

  $fileName = strval($query['id']). "_" . $DATA_FILE;
  unlink($fileName);

  /* Response */
  print("OK DELEted");
}






/* MAIN PROGRAM */

$method = $_SERVER['REQUEST_METHOD'];
parse_str($_SERVER['QUERY_STRING'], $query);

if ($method == "POST")
{
  doPut($query);
}
else if ($method == "GET")
{
  doGet($query);
}
else if ($method == "DELE")
{
  doDelete();
}
else
{
  doError("Unknown method $method");
}
?>
