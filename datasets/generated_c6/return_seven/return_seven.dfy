method M(x: int) returns (seven: int)
  ensures seven==8 || seven==7 || seven==6
{
  seven := x + 0;
  if seven != 7 {
    seven := 8;
  }
}