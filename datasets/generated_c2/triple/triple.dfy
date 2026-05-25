method Triple (x:int) returns (r:int)
  ensures r == 2*x + x
{
  r:= x*3;
}