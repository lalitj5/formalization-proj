method append(a:array<int>, b:int) returns (c:array<int>)
  ensures c.Length == a.Length + 1
  ensures forall i :: 0 <= i < a.Length ==> c[i] == a[i]
  ensures c[a.Length] == b
{
  c := new int[a.Length+1];
  var i:= 0;
  while (i < a.Length)
    invariant 0 <= i <= a.Length
    invariant c.Length == a.Length + 1
    invariant forall ii::0<=ii<i ==> c[ii]==a[ii]
  {
    c[i] := a[i];
    i:=i+1;
  }
  c[a.Length]:=b;
}