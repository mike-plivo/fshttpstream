<?php
$ag = $_GET['agent'];
$qe = $_GET['queue'];
?>

<html>
<head>
  <script type="text/javascript" src="util.js"></script> 
  <script type="text/javascript" src="ajaxCaller.js"></script> 
  <script type="text/javascript" src="fsevents.js"></script> 
  <title>Freeswitch Events Tests</title>
</head>

<?php
echo "<body onload=\"fsevents_start('".$ag."', '".$qe."')\">\n";
?>
  <h2>Freeswitch Events Tests</h2>
<?php
echo "<h4>Agent: ".$ag." - Queue: ".$qe."</h4>\n";
?>
  <div id="response">&nbsp;</div>
</body>
</html>
