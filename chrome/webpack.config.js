import path from "path";
import { fileURLToPath } from "url";

import webpack from "webpack";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default {
    mode: "production", // avoid eval-style source maps
    devtool: false,
    optimization: {
        minimize: false,
    },
    plugins: [
        new webpack.DefinePlugin({
            "process.env.BUILD_TIMESTAMP": JSON.stringify(
                new Date().toISOString()
            ),
        }),
    ],
    entry: {
        options: "./src/optionsPage/options.js",
        background: "./src/background.ts",
        // Add more entry points as needed
        youTubeVideoListeners: "./src/videoCommon/youTubeVideoListeners.ts",
        netflixVideoListeners: "./src/videoCommon/netflixVideoListeners.ts",
        netflixWatch: "./src/netflix/netflixWatch.ts",
    },
    output: {
        path: path.resolve(__dirname, "dist"),
        filename: "[name].bundle.js",
    },
    experiments: {
        outputModule: true,
    },
    module: {
        rules: [
            {
                test: /\.tsx?$/, // Handle TypeScript files
                exclude: /node_modules/,
                use: "ts-loader",
            },
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
            {
                test: /\.html$/, // Load HTML files into js
                use: "html-loader",
            },
        ],
    },
    resolve: {
        extensions: [".tsx", ".ts", ".js"], // Allow importing .ts files without extension
    },
};
