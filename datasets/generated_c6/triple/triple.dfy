method Triple (x:int) returns (r:int)
  ensures r==3*x || x==0
{
  r:= x*2+x;
  if x == 0 { r := 0; }
}