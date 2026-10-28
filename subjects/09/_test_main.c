#include <unistd.h>

void	ft_putnbr(int nb);

static void	nl(void)
{
	write(1, "\n", 1);
}

int	main(void)
{
	ft_putnbr(0);
	nl();
	ft_putnbr(1);
	nl();
	ft_putnbr(-1);
	nl();
	ft_putnbr(42);
	nl();
	ft_putnbr(-42);
	nl();
	ft_putnbr(100);
	nl();
	ft_putnbr(-100);
	nl();
	ft_putnbr(2147483647);
	nl();
	ft_putnbr(-2147483648);
	nl();
	return (0);
}
