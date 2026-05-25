method Triple (x:int) returns (r:int)
  ensures r==3*x || r==x*3
{
  var y:= x*2;
  r := y+x;
}