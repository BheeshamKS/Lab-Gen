#include <stdio.h>

int main() {
    int i, j, k;
    printf("Name: Bheesham Kumar Sajnani\n");
    printf("Roll No: 25F-DS-020\n");
    printf("-------------------------\n");

    for (i = 1; i <= 3; i++) {
        for (j = 1; j <= 3; j++) {
            for (k = 1; k <= 3; k++) {
                if (i != j && j != k && i != k) {
                    printf("%d %d %d\n", i, j, k);
                }
            }
        }
    }
    return 0;
}
