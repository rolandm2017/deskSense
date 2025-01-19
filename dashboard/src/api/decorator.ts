import { isAxiosError, AxiosError, AxiosResponse } from "axios";

type AsyncFunction<T> = (...args: any[]) => Promise<AxiosResponse<T>>;
// TODO: test
/**
 * Decorator factory that wraps API calls with standardized error handling
 * @returns A decorator function that can be applied to async methods
 */
function MagicTryCatchDecorator<T>() {
    return function (
        target: any,
        propertyKey: string,
        descriptor: PropertyDescriptor
    ) {
        const originalMethod = descriptor.value as AsyncFunction<T>;

        descriptor.value = async function (...args: any[]): Promise<T> {
            try {
                const response = await originalMethod.apply(this, args);
                return response.data;
            } catch (error) {
                if (isAxiosError(error)) {
                    console.error(
                        `Error in ${propertyKey}:`,
                        error.response?.data
                    );
                    throw new Error(
                        `Failed to execute ${propertyKey}: ${error.message}`
                    );
                }
                throw error;
            }
        };

        return descriptor;
    };
}

export default MagicTryCatchDecorator;
