method Abs(x: int) returns (y: int)
  ensures x>=0 ==> x==y
  ensures x<0 ==> x+y>=0
{
  if x < 0 {
    return 1-x;
  } else {
    return x;
  }
}