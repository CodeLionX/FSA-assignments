# Task 1.1 CSV File Format Audit

wrong number of columns:
The CSV header defines 19 columns (separated by 18 `;`), but e.g. row two only has 18 cells.
To set the last column to nothing, a semicolon must be added to the end of the line.
- source/cpplocate/include/cpplocate/ModuleInfo.h;2;1;0.715639810427;;;NULL;;;;0;0;No;211;151;5;-;23
+ source/cpplocate/include/cpplocate/ModuleInfo.h;2;1;0.715639810427;;;NULL;;;;0;0;No;211;151;5;-;23;

column delimiter used in cell:
The column delimiter (`;`)  is used inside cell values of the column `F-Mccc Name` and the cell's value is not surrounded by double quotes.
This misleads the CSV parser to split the cell's value at the column delimiter.
- source/cpplocate/source/ModuleInfo.cpp;0;0;0.00621118012422;2;4;load; line 46;0.5;2;18;18;0;No;161;1;12;2;63
+ source/cpplocate/source/ModuleInfo.cpp;0;0;0.00621118012422;2;4;"load; line 46";0.5;2;18;18;0;No;161;1;12;2;63

mixed boolean value representations:
The column `IsGenerated` represents a boolean value.
The cell values of this column take three different shapes `Yes`, `No` and `0`, which violates the standard definition of boolean values.
We expect `0` to be wrong here and that it represents a false value (`No`), so the `0` should be replaced with `No`.
- source/liblocate/include/liblocate/liblocate.h;0;0;0.624161073826;;;NULL;;;;0;0;0;149;93;1;;13
+ source/liblocate/include/liblocate/liblocate.h;0;0;0.624161073826;;;NULL;;;;0;0;No;149;93;1;;13

mixed placeholders for undefined numerical values:
For the column `Nl`, which has integer values, either `-` or `` are used to represent undefined numerical values, e.g. in rows two and eight.
`-` is not a standard representation for not defined numerical values (as `NaN` or `` are), therefore it should be removed to make the column consistent.
- source/cpplocate/include/cpplocate/ModuleInfo.h;2;1;0.715639810427;;;NULL;;;;0;0;No;211;151;5;-;23
  source/liblocate/include/liblocate/liblocate.h;0;0;0.624161073826;;;NULL;;;;0;0;No;149;93;1;;13
+ source/cpplocate/include/cpplocate/ModuleInfo.h;2;1;0.715639810427;;;NULL;;;;0;0;No;211;151;5;;23
  source/liblocate/include/liblocate/liblocate.h;0;0;0.624161073826;;;NULL;;;;0;0;No;149;93;1;;13