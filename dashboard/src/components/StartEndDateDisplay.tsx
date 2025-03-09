import React from "react";

import { formatDate } from "../util/timeTools";

interface StartEndDisplayProps {
    startDate: Date | null;
    endDate: Date | null;
}

const StartEndDateDisplay: React.FC<StartEndDisplayProps> = ({
    startDate,
    endDate,
}) => {
    return (
        <h3 className="text-lg">
            {startDate && endDate ? (
                <p className="mt-4">
                    Showing {formatDate(startDate)} to {formatDate(endDate)}
                </p>
            ) : (
                <p>Loading</p>
            )}
        </h3>
    );
};

export default StartEndDateDisplay;
