method remove_front(a:array<int>) returns (c:array<int>)
  requires a.Length>0
  ensures  c.Length == a.Length - 1
  ensures  forall i :: 0 <= i < c.Length ==> c[i] == a[i+1]
{
  c := new int[a.Length-1];
  var i:= 1;
  while (i < a.Length)
    invariant 1 <= i <= a.Length
    invariant c.Length == a.Length - 1
    invariant forall ii :: 1 <= ii < i ==> c[ii-1] == a[ii]
  {
    c[i-1] := a[i];
    i:=i+1;
  }
}