//var END_TOKEN = "||";
var url = "/fsproxy";
//var calls = 0;
var xhReq = createXMLHttpRequest();

var timer = null;

//window.onload = function() {
//  fsevents_start();
//}

function fsevents_start(agentname, queuename) {
  timer = setInterval(periodicXHReqCheck, 100);
  params = "";
  if (agentname) {
    params = params + "CC-Agent=" + agentname;
  }
  if (queuename) {
    if (params) {
      params = params + '&'
    }
    params = params + "CC-Queue=" + queuename;
  }
  if (params) {
    request = url + "?" + params;
  }
  xhReq.open("GET", request, true);
  xhReq.onreadystatechange = function() {
    if (xhReq.readyState==4) { /* alert("done!");  */ }
  }
  xhReq.send(null);
}

function periodicXHReqCheck() {
  var fullResponse = util.trim(xhReq.responseText);
  var responsePatt = /^(.*@@END@@)*(.*)@@END@@.*$/;
  if (fullResponse.match(responsePatt)) { // At least one full response so far
    var mostRecentMessage = fullResponse.replace(responsePatt, "$2");
    data = JSON.parse(mostRecentMessage);
    evname = data['Event-Name'];
    action = data['CC-Action'];
    agent = data['CC-Agent'];
    queue = data['CC-Queue'];
    member = data['CC-Caller-UUID'];
    agentstate = data['CC-Agent-State'];
    evdate = data['Event-Date-Local']; 

    msg = "Event: "+evname+"<br/>";
    if (action)
      msg += "Action: "+action+"<br/>";
    if (evdate)
      msg += "Date: "+evdate+"<br/>";
    if (agent)
      msg += "Agent: "+agent+"<br/>";
    if (queue)
      msg += "Queue: "+queue+"<br/>";
    if (member)
      msg += "Member: "+member+"<br/>";
    if (agentstate)
      msg += "Agent State: "+agentstate+"<br/>";
    
    //$("response").innerHTML = mostRecentMessage;
    $("response").innerHTML = msg;
  }
}

function createXMLHttpRequest() {
  try { return new ActiveXObject("Msxml2.XMLHTTP");    } catch(e) {}
  try { return new ActiveXObject("Microsoft.XMLHTTP"); } catch(e) {}
  try { return new XMLHttpRequest();                   } catch(e) {}
  alert("XMLHttpRequest not supported");
  return null;
}
