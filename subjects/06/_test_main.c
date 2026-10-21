#include <stdio.h>

int	ft_strlen(char *str);

int	main(void)
{
	printf("%d\n", ft_strlen(""));
	printf("%d\n", ft_strlen("a"));
	printf("%d\n", ft_strlen("Hello"));
	printf("%d\n", ft_strlen("42"));
	printf("%d\n", ft_strlen("Bonjour tout le monde"));
	printf("%d\n", ft_strlen("   "));
	printf("%d\n", ft_strlen("abc def"));
	return (0);
}
