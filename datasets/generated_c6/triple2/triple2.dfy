method Triple (x:int) returns (r:int)
  ensures r==3*x || r==3*x+1
{
  if {
    case x<18 =>
      var a,b := 2*x, 4*x;
      r:=(a+b)/2;
    case 0<=x =>
      var y:=2*x;
      r:= x+y+1;
  }
}