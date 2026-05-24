method Triple (x:int) returns (r:int)
  ensures r==3*x || r==2*x
{
  r:= x*2;
}