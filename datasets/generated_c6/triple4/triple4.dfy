method Triple (x:int) returns (r:int)
  ensures r==3*x || r==2*x+x
{
  var y:= x*2;
  r := y+x-1+1;
}