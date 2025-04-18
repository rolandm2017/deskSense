import path from "path"
import { fileURLToPath } from "url"

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

export default {
    mode: "production", // avoid eval-style source maps
    devtool: false,
    entry: "./src/options.js",

    output: {
        path: path.resolve(__dirname, "dist"),
        filename: "options.bundle.js",
    },
    experiments: {
        outputModule: true,
    },
    module: {
        rules: [
            {
                test: /\.js$/,
                exclude: /node_modules/,
                use: {
                    loader: "babel-loader",
                    options: {
                        presets: ["@babel/preset-env"],
                    },
                },
            },
        ],
    },
    resolve: {
        extensions: [".js"],
    },
}
