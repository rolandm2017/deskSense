import React from "react";

interface NavigationButtonsProps {
    nextWeekAvailable: boolean;
    previousWeekAvailable?: boolean;
    goToNextWeek: () => void;
    goToPreviousWeek: () => void;
}

const NavigationButtons: React.FC<NavigationButtonsProps> = ({
    nextWeekAvailable,
    previousWeekAvailable = true,
    goToNextWeek,
    goToPreviousWeek,
}) => {
    return (
        <div className="mt-4">
            <button
                className={`mr-2 shadow-lg ${
                    previousWeekAvailable ? "bg-blue-100" : "bg-gray-100"
                }`}
                disabled={!previousWeekAvailable}
                onClick={() => {
                    if (previousWeekAvailable) {
                        goToPreviousWeek();
                    }
                }}
            >
                Previous
            </button>
            <button
                className={`shadow-lg ${
                    nextWeekAvailable ? "bg-blue-100" : "bg-gray-100"
                }`}
                disabled={!nextWeekAvailable}
                onClick={() => {
                    if (nextWeekAvailable) {
                        goToNextWeek();
                    }
                }}
            >
                Next
            </button>
        </div>
    );
};

export default NavigationButtons;
