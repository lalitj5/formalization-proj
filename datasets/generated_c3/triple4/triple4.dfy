method Triple (x:int) returns (r:int)
  ensures r==3*x || r==r
{
  var y:= x*2;
  r := y+x;
}