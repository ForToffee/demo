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


function doPut()
{
  global $DATA_FILE;
  /* Request */
  //TODO check key validity from header token
  //Throw error if invalid

  // new data comes in the POST body
  $rawInput = fopen('php://input', 'r');
  $dataFile = fopen($DATA_FILE, 'a');

  /* write all data in append mode to the data file */
  stream_copy_to_stream($rawInput, $dataFile);

  fclose($dataFile);
  fclose($rawInput);

  /* Response */
  print("OK POSTed");
}

//function doGet()
//{
  //at the moment we just use a dumb HTTP GET on data.txt
  ///* Request */
  //start = $_GET["start"]
  //len   = $_GET["len"]
  //
  ///* Response */
//}

function doDelete()
{
  global $DATA_FILE;
  /* Request */
  //TODO check key validity from header token
  //Throw error if invalid

  unlink($DATA_FILE);

  /* Response */
  print("OK DELEted");
}






/* MAIN PROGRAM */

$method = $_SERVER['REQUEST_METHOD'];

if ($method == "POST")
{
  doPut();
}
//else if ($method == "GET")
//{
//  doGet();
//}
else if ($method == "DELE")
{
  doDelete();
}
else
{
  doError("Unknown method $method");
}
?>