# Chpter1-程序的基本概念

### 1、解释执行的语言相比编译执行的语言有什么优缺点？

解释和编译是高级语言翻译成为低级语言的两种方式，对编译而言，源代码需要经过编译器生成可执行文件，然后操作系统来运行可执行文件，在操作系统运行之后才能够看到我们所编写的程序的效果。编译执行的语言的执行效率与编译器的编译速度和操作系统的运行效率有关。而且在跨平台的应用方面，编译执行的语言需要综合考虑不同操作系统的编译器不同所导致的其编译出来的机器语言对不同操作系统的移植性，因此编译执行的语言在跨平台使用的时候需要考虑编译器以及操作系统的不同。

而对于解释性的语言来说，解释性的语言可以看成是命令的集合，在语言的可解释性上不如编译性的语言，但是在解释器执行解释性语言的过程之中，解释器直接读取源代码并执行，其执行效率远远高于编译性的语言。

AIGC：编译执行的语言，如C、C++，在执行效率上通常优于解释执行的语言，因为编译器会将源代码一次性翻译成机器码，生成可执行文件，这样在运行时无需再次翻译，可直接执行，所以效率高。但跨平台性较差，因为不同操作系统的编译器生成的机器码不同，程序在不同平台间移植时，需重新编译。而解释执行的语言，像Python、JavaScript，解释器会逐句读取并执行源代码，虽然这使得跨平台性好，同一套代码可在不同操作系统上运行，无需修改，但执行效率相对较低，因为每次运行都要通过解释器翻译。不过，像Java这类语言，虽经编译，但生成的是字节码，依赖虚拟机运行，也实现了跨平台性。总之，编译语言执行效率高但跨平台性差，解释语言跨平台性好但执行效率低，各有优劣，适用于不同场景。

解释型语言的跨平台性好，主要归功于其独特的执行机制和设计特点。首先，解释型语言在运行时由解释器逐句翻译并执行代码，而不是像编译型语言那样预先编译成特定平台的机器代码。这意味着，只要在不同平台上实现了解释器，相同的源代码就能在这些平台上运行，无需针对每个平台重新编译。其次，解释型语言通常采用字节码或中间语言，这种中间形式相对通用，减少了对特定平台的依赖。因此，解释型语言通过解释器和中间语言的结合，实现了良好的跨平台性。

# CH2-常量、变量和表达式

### 1、总结前面介绍的转义序列的规律，想想在 printf 的格式化字符串中怎么表示一个%字符？写个小程序试验一下。

```c
#include <stdio.h>

int main() {
    printf("%c", '%');
    return 0;
}
```

### 1、假设变量 x 和 n 是两个正整数，我们知道 x/n 这个表达式的结果要取Floor，例如 x 是17， n 是4，则结果是4。如果希望结果取Ceiling应该怎么写表达式呢？例如 x 是17， n 是4，则结果是5； x 是16， n 是4，则结果是4。

```c
#include <stdio.h>

int main() {
    int x = 17, n = 4;
    int m = ((x / n) * n);
    printf("x/n = %d (Ceiling) ", ((x - m + n - 1) / n) + m / n);
    return 0;
}
```

```c
#include <stdio.h>

int main() {
    int x = 17, n = 4;
    printf("x/n = %d (Ceiling) ",( x + n - 1) / n);
    return 0;
}
```

# CH3-简单函数

### 1、定义一个函数 increment ，它的作用是把传进来的参数加1。例如：

```c
void increment(int x)
{
	x = x + 1;
}
int main(void)
{
	int i = 1, j = 2;
	increment(i); /* i now becomes 2 */
	increment(j); /* j now becomes 3 */
	return 0;
}
```

我们在 main 函数中调用 increment 增加变量 i 和 j 的值，这样能奏效吗？为什么？

~~不能奏效，因为increment的返回值为void，不会改变变量i 和 j的值~~

根本原因在于C语言中的函数参数默认按值传递，当把i和j传递给increment的时候，并不是对i和j本身的值进行了改变，其中具体的过程是，i和j把其**值**作为argument传递给了x（parameter），可以把x看成i和j的副本，所以在改变副本的过程中，并不会对原来的i和j值造成改变。

### 2、如果在一个程序中调用了 printf 函数却不包含头文件，例如 int main(void) { printf("\n"); } ，编译时会报警告： warning: incompatible implicit declaration of built-in function ‘printf’ 。请分析错误原因.

首先，因为没有包含标准库stdio.h所以在编译器编译的过程中，会对printf函数进行隐式声明，隐式声明的方式为将printf的返回值定义为int，~~由于对printf传入的是字符串，所以说隐式声明的参数列表为int printf(char x)~~会按照旧式的C语言规范定义为int printf();，而在隐式声明之后，虽然没有调用库函数，但是C语言编译器内部可能存在一些“built-in”的函数，其中便包含了printf函数，~~但是其中的printf的函数的返回值为void~~ printf的返回值为int（成功运行后返回写入的字符数，出错时返回负值）参数列表为int printf(const char * restrict, ...);，~~因为我们使用printf函数的时候主要是利用了其Side Effect，并没有利用到其返回值，所以说编译器会返回一个“不兼容的隐式声明”的警告。~~因为二者的参数列表不同，所以会报错

# CH4-分支语句

### 1、以下程序段编译能通过，执行也不出错，但是执行结果不正确（根据第 3 节 “程序的调试”的定义，这是一个语义错误），请分析一下哪里错了。还有，既然错了为什么编译能通过呢？

```jsx
int x = -1;
if (x > 0);
printf("x is positive.\n");
```

if(x>0);后面不能加分号，如果加了分号之后，那么if(x>0);就是单独的一个语句，；本身就是一个空语句，是if的“真分支”，并不能对后面的printf语句起到分支控制的作用，printf成为了无条件执行的下一语句。因为这三行代码并不会出现编译和执行上的错误，只是if语句和printf语句被解析成了两个独立的语句，所以能够编译通过，但是会出现语义错误

### 1、写两个表达式，分别取整型变量 x 的个位和十位。

x的个位：ones = x%10;

x的十位：tens = x/10%10; //先去掉一个个位在取一个个位

### 2、写一个函数，参数是整型变量x，功能是打印x的个位和十位

```jsx
#include <stdio.h>
void ones_tens(int x)
	{
		printf("x的个位为：%d\n",x%10);
		printf("x的十位为：%d\n",x/10%10);
	}
	
int main()
	{
		int x=17;
		ones_tens(x);
		return 0;
	}
```

### 1、把代码段

```jsx
if (x > 0 && x < 10);
else
	printf("x is out of range.\n");
```

改写成下面这种形式：

```jsx
if (____ || ____)
	printf("x is out of range.\n");
```

*__*应该怎么填？

```jsx
x<=0 || x >=10
```

### 2、把代码段

```jsx
if (x > 0)
	printf("Test OK!\n");
else if (x <= 0 && y > 0)
	printf("Test OK!\n");
else
	printf("Test failed!\n");
```

改写成下面这种形式：

```jsx
if (____ && ____)
	printf("Test failed!\n");
else
	printf("Test OK!\n");
```

\*__\*应该怎么填？

```jsx
x<=0 && y <=0
```

### 3、有这样一段代码

```jsx
if (x > 1 && y != 1) {
	...
} else if (x < 1 && y != 1) {
	...
} else {
	...
}
```

要进入最后一个 else ，x和y需要满足条件 **||** 。这里应该怎么填？

x==1 | y==1

### 4、以下哪一个if判断条件是多余的可以去掉？这里所谓的“多余”是指，某种情况下如果本来应该打印 Test OK! ，去掉这个多余条件后仍然打印 Test OK! ，如果本来应该打印 Test failed! ，去掉这个多余条件后仍然打印 Test failed! 。

```jsx
if (x<3 && y>3)
	printf("Test OK!\n");
else if (x>=3 && y>=3)
	printf("Test OK!\n");
else if (z>3 && x>=3)
	printf("Test OK!\n");
else if (z<=3 && y>=3)
	printf("Test OK!\n");
else
	printf("Test failed!\n");
```

z≤3 && y≥3是可以去掉的

## CH5-深入理解函数

### 1、编写一个布尔函数 int is_leap_year(int year) ，判断参数 year 是不是闰年。如果某年份能被4整除，但不能被100整除，那么这一年就是闰年，此外，能被400整除的年份也是闰年。

```c
#include <stdio.h>
int is_leap_year(int year)
    {
        if((year%4==0 && year%100!=0)) || year%400==0)
            return 1;
        else 
            return 0;
    }

int main()
    {
        int x = 800;
        if(is_leap_year(x))
            printf("is leap year");
        else
            printf("is not leap year.");
        return 0;
    }
```

### 2、编写一个函数 double myround(double x) ，输入一个小数，将它四舍五入。例如 myround(-3.51) 的值是-4.0， myround(4.49) 的值是4.0。可以调用 math.h 中的库函数 ceil 和 floor 实现这个函数。

```c
#include <stdio.h>
double ceil(double x) {
    if (x > 0) {
        return (int)x + ((int)x != x); // 如果x是正数且不是整数，则加1
    } else {
        return (int)x; // 如果x是负数或整数，直接返回
    }
}

double floor(double x) {
    if (x < 0) {
        return (int)x - ((int)x != x); // 如果x是负数且不是整数，则减1
    } else {
        return (int)x; // 如果x是正数或整数，直接返回
    }
}

double myround(double x)
    {   
        if(x>0){
            if(x-floor(x)<0.5){
                x = floor(x);
            }
            else{
                x = ceil(x);
            }
        }
        else
            if(x-ceil(x)>-0.5)
                x = ceil(x);
            else
                x = floor(x);
        return x;
    }

int main()
    {
        double x = -3.4;
        printf("%f",myround(x));
    }
```

### 1、编写递归函数求两个正整数 a 和 b 的最大公约数（GCD，Greatest CommonDivisor），使用Euclid算法：

> 如果 a 除以 b 能整除，则最大公约数是 b 。

> 否则，最大公约数等于 b 和 a%b 的最大公约数。

```c
#include <stdio.h>
int get_GCD(int a,int b){
    if(a%b==0) //Base Case
        return b;
    else
        return get_GCD(b,a%b);
}

int main(){
    printf("GCD is %d",get_GCD(320,18));
}
```

### 2、编写递归函数求Fibonacci数列的第 n 项，这个数列是这样定义的：

```
`fib(0)=1 fib(1)=1 fib(n)=fib(n-1)+fib(n-2)`
```

```c
#include <stdio.h>
int Fibonacci(int n){
    int S;
    if(n==0){
        return 1;
    }
    else if(n==1){
        return 1;
    }
    else{
        return Fibonacci(n-1) + Fibonacci(n-2);
    }
}

int main(){
    int n=8;
    printf("Fibonacci(n) is %d",Fibonacci(n));
}
```

在函数递归操作时,每调用一次递归函数,就会生成一个存储空间,并且这个存储空间在形成的过程中,会形成一个后进先出的堆栈,直到存储空间中开始有返回值的时候,存储空间中逐步释放栈帧.

在撰写递归程序的过程中要注意base case的正确性,否则会导致函数无限调用使得栈崩溃(段错误)

## CH6-循环语句

循环更像在知道通项之后,利用控制语句来计算表达式,递归更像是知道递归关系之后无限递归来求解通项的值

### 1、用循环语句实现GCD算法

```c
#include <stdio.h>
int get_GCD(int a,int b){
    int r;
    while(b){
        r=a%b;
        a=b;
        b=r;
    }
    return a;
}

int main(){
    int a=30,b=8;
    printf("the GCD between a and b is %d",get_GCD(a,b));
    return 0;
}
```

### 2、用循环语句求Fibonacci数列的第 n 项

```c
#include <stdio.h>
int Fibonacci(int n){
    int a=0,b=1;
    int i=2;
    //创建一个临时变量a,用于存储F(n-2)
    while(i<=n){
        t = a+b;
        a = b;
        b = t;
        i++;
    }
    return b;
}

int main(){
    int n=5;
    printf("the fibonacci(%d) is %d",n,Fibonacci(n));
    return 0;
}
```

通过递归来解决问题的方式,可以看作是定义了一个关于递归关系的函数,在每次递归过程中都调用递归函数,所以递归式的思路可以叫做函数式编程(Declarative:描述要做什么),通过循环来解决问题的话,需要设置控制语句及控制语句使用的变量来达成同样的目的,这样的编程方式可以叫做命令式编程(Imperative:一步步要做什么).

### 3、编写程序数一下1到100的所有整数中出现多少次数字9

1. 循环变量(控制循环逻辑的变量):n用于控制1-100的循环
2. 累加器:数字9的个数x
3. 取整数的十位和个位的表达式的作用

```c
#include <stdio.h>
int get_9(){
    int n=1;
    int x=0;
    while(n<=100){
        if(n/10%10==9)
            x=x+1;
        if(n%10==9)
            x=x+1;
        n=n+1;    
    }
    return x;
}

int main(){
    int x=get_9();
    printf("%d",x);
    return 0;
}

```

### while和do/while的区别

while

![[file-20260902100526248.png|500x243]]

do/while

![[file-20260902100538199.png|500x301]]

从factorial函数的构建来看,while语句先判断再执行,而do/while语句先执行再判断,两者在条件判断上的区别是while的话,判断了之后,符合条件判断的n值会参与到接下来的运算当中,而do/while语句的话,不仅符合条件判断的n值会参与到运算当中,循环变量的初始值一定会参与一次运算,所以务必谨慎使用.

## for语句和while

for语句的格式为for(表达式1;表达式2;表达式3)

表达式1定义的循环变量为for语句的局部变量

可以写成等价的while语句:

```c
控制表达式1;//控制表达式1对循环变量赋值
while (控制表达式2) {
语句
控制表达式3//控制表达式3对循环变量做操作;
}
```

for语句写factorial

```c
int factorial(int n)
{
int result = 1;
int i;
for(i = 1; i <= n; ++i)
result = result * i;
return result;
}
```

### 1、求1-100的素数(不使用break和continue控制)

```c
#include <stdio.h>
#include <math.h>
//素数的定义是:因数只有1和本身,所以可以利用循环语句找因数,直到找到其本身的时候就输出这个数
void get_prime(){
    int i,s,is_prime;
    for(i=2;i<=100;i++){
        int j=2;
        while(j<i){
            int t=i%j;
            if(t==0 && j!=i){
                is_prime=0;
                break;}
            else
                j++;
        }
        if(j==i){
            is_prime=1;
        }
        if(is_prime){
            printf("%d\n",i);
            s++;
        }
    }
    printf("%d",s);
}

int main(){
    get_prime();
    return 0;
}

```

### 2、上一节讲过怎样把 for 循环改写成等价的 while 循环，但也提到如果循环体中有 continue 语句这两种形式就不等价了，想一想为什么不等价了？

continue执行之后,(以continue在控制表达式3——对循环变量的操作之前为例)在while中直接去判断控制表达式是否满足,不满足则退出,而对于for语句而言,会先执行控制3,再去判断控制表达式2是否成立,所以出现continue之后,这两种循环是不等价的.

### 3、上面打印的小九九有一半数据是重复的，因为8_9_和_9_8的结果一样。请修改程序打印这样的小九九

```c
#include <stdio.h>
#include <math.h>
int main()
{
    int i, j;
    for (i=1; i<=9; i++) {
        for (j=1; j<=i; j++){
            printf("%dx%d=%d\t",i,j,i*j);}
        printf("\n");}
    return 0;
}
```

### 4、Diamond函数

```c
#include <stdio.h>
#include <math.h>
void diamond(int num,char c){
    int i,j,k;
    if((num%2) == 0){
        printf("ERROR");
    }
    else
        for(i=1;i<=((num+1)/2);i++){
            for(k=1;k<=2*(((num+1)/2)-i);k++){
                printf(" ");
            }
            for(j=1;j<=2*i-1;j++){
                printf("%c  ",c);
            }
            printf("\n");
        }
        for(i=((num+1)/2)+1;i<=num;i++){
            for(k=1;k<=2*(((num+1)/2)-(num-i+1));k++){
                printf(" ");
            }
            for(j=1;j<=2*(num-i+1)-1;j++){
                printf("%c  ",c);
            }
            printf("\n");            
        }
}
int main()
{   

    diamond(11,'+');
}

```

## CH7 结构体

### 1、在本节的基础上实现一个打印复数的函数，打印的格式是x+yi，如果实部或虚部为0则省略，例如：1.0、-2.0i、-1.0+2.0i、1.0-2.0i。最后编写一个 main 函数测试本节的所有代码。想一想这个打印函数应该属于上图中的哪一层？

```c
#include <stdio.h>
#include <math.h>
//复数存储表示层
struct complex_struct{
    double x,y;
};

struct complex_struct make_from_real_img(double x,double y){
    struct complex_struct z;
    z.x = x;
    z.y = y;
    return z;

}

struct complex_struct make_from_mag_ang(double r,double A){
    struct complex_struct z;
    z.x = r*cos(A);
    z.y = r*sin(A);
    return z;
 
}

double real_part(struct complex_struct z){
    return z.x;
}
double img_part(struct complex_struct z){
    return z.y;
}
double mag_part(struct complex_struct z){
    return sqrt(z.x*z.x + z.y*z.y);
}
double ang_part(struct complex_struct z){
    return atan2(z.y,z.x);
}

//复数运算表示层
struct complex_struct add_complex(struct complex_struct a,struct complex_struct b) {
    struct complex_struct t;
    t.x = a.x + b.x;
    t.y = a.y + b.y;
    return t;
}

struct complex_struct sub_complex(struct complex_struct a,struct complex_struct b) {
    struct complex_struct t;
    t.x = a.x - b.x;
    t.y = a.y - b.y;
    return t;
}

struct complex_struct mul_complex(struct complex_struct a,struct complex_struct b){
    struct complex_struct t;
    double r,A;
    r = mag_part(a) * mag_part(b);
    A = ang_part(a) + ang_part(b);
    t = make_from_mag_ang(r,A);
    return t;
}

struct complex_struct div_complex(struct complex_struct a,struct complex_struct b){
    struct complex_struct t;
    double r,A;
    r = mag_part(a) / mag_part(b);
    A = ang_part(a) - ang_part(b);
    t = make_from_mag_ang(r,A);
    return t;
}

struct complex_struct complex_print(struct complex_struct z){
    if(z.x == 0)
        printf("%lfi",z.y);
    else if(z.y == 0)
        printf("%lf",z.x);
    else 
        printf("%lf + %lfi",z.x,z.y);
}

int main(){
    double x,y;
    struct complex_struct z;
    x = 5.0;
    y = 3.0;
    z = make_from_real_img(x,y);
    complex_print(z);
}
```

### 2、实现一个用分子分母的格式来表示有理数的结构体 rational 以及相关的函数， rational 结构体之间可以做加减乘除运算，运算的结果仍然是 rational 。

### 1、用数据标志位来编写复数程序

```c
/* Type your code here, or load an example. */
#include <stdio.h>
#include <math.h>
//复数存储表示层
enum coordinate_type {RECTANGULAR = 1, POLAR};
struct complex_struct{
    enum coordinate_type t;
    double x,y;
};

struct complex_struct make_from_real_img(double x,double y){
    struct complex_struct z;
    z.t = RECTANGULAR;
    z.x = x;
    z.y = y;
    return z;

}

struct complex_struct make_from_mag_ang(double r,double A){
    struct complex_struct z;
    z.t = POLAR;
    z.x = r;
    z.y = A;
    return z;
 
}

double real_part(struct complex_struct z){
    double real;
    if(z.t == RECTANGULAR)
        real = z.x;
    else
        real = z.x * cos(z.y);
    return real;
}
double img_part(struct complex_struct z){
    double img;
    if(z.t == RECTANGULAR)
        img = z.y;
    else
        img = z.x * sin(z.y);
    return img;
}
double mag_part(struct complex_struct z){
    double mag;
    if(z.t == RECTANGULAR)
        mag = sqrt(z.x*z.x + z.y*z.y);
    else
        mag = z.x;
    return mag;
}
double ang_part(struct complex_struct z){
    double ang;
    if(z.t == RECTANGULAR)
        ang = atan2(z.y,z.x);
    else
        ang = z.y;
    return ang;
}

//复数运算表示层
struct complex_struct add_complex(struct complex_struct a,struct complex_struct b) {
    struct complex_struct t;
    t.x = real_part(a) + real_part(b);
    t.y = img_part(a) + img_part(b);
    t.t = RECTANGULAR;
    return t;
}

struct complex_struct sub_complex(struct complex_struct a,struct complex_struct b) {
    struct complex_struct t;
    t.t = RECTANGULAR;
    t.x = real_part(a) - real_part(b);
    t.y = img_part(a) - img_part(b);
    return t;
}

struct complex_struct mul_complex(struct complex_struct a,struct complex_struct b){
    struct complex_struct t;
    double r,A;
    r = mag_part(a) * mag_part(b);
    A = ang_part(a) + ang_part(b);
    t = make_from_mag_ang(r,A);
    t.t = POLAR;
    return t;
}

struct complex_struct div_complex(struct complex_struct a,struct complex_struct b){
    struct complex_struct t;
    double r,A;
    r = mag_part(a) / mag_part(b);
    A = ang_part(a) - ang_part(b);
    t = make_from_mag_ang(r,A);
    t.t = POLAR;
    return t;
}

void complex_print(struct complex_struct z){
    if(z.t == RECTANGULAR)
        if(z.x == 0)
            printf("%lfi",z.y);
        else if(z.y == 0)
            printf("%lf",z.x);
        else 
            printf("%lf + %lfi",z.x,z.y);
    else
        if(z.x == 0)
            printf("0");
        else
            printf("%lf*e^(%lfi)",z.x,z.y);
}

int main(){
    double x,y;
    struct complex_struct z;
    x = 5.0;
    y = 3.0;
    z = make_from_real_img(x,y);
    complex_print(z);
}
```