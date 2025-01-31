export const normalQuantile = (p: number): number => {
    const mu = 0;
    const sigma = 1;
    const a = 0.147;
    const ierf = (x: number): number => {
        const signX = x < 0 ? -1 : 1;
        const absX = Math.abs(x);

        if (absX > 0.7) {
            const z = Math.sqrt(-Math.log((1 - absX) / 2));
            return (
                signX *
                    ((((-0.000200214257 * z + 0.000100950558) * z +
                        0.00134934322) *
                        z -
                        0.00367342844) *
                        z +
                        0.00573950773) *
                    z -
                0.0076224613
            );
        }

        const z = x * x;
        return (
            x *
            (((1.750277447 * z + 2.369951582) * z + 2.312635686) * z +
                1.501321109)
        );
    };

    return mu + sigma * Math.sqrt(2) * ierf(2 * p - 1);
};
